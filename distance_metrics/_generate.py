import glob
from textwrap import dedent, indent
from os.path import join, basename
from pathlib import Path

PY_TAB = "    "
GENERATED_DIR = "distance_metrics/src/generated/"
DEFINITIONS_DIR = "distance_metrics/definitions/"

# All SIMD instructions supported by xsimd
_x86 = [
    "sse2",
    "sse3",
    "ssse3",
    "sse4_1",
    "sse4_2",
    "avx",
    "avx2",
    "avx512bw",
    "avx512cd",
    "avx512dq",
    "avx512f",
    "fma3<xs::avx>",
    "fma3<xs::avx2>",
    "fma3<xs::sse4_2>",
    "fma4",
]
_ARM = [
    "neon",
    "neon64",
]


def _make_architectures(target_arch):
    target_system = None
    for _ARCH in (_x86, _ARM):
        try:
            target_arch_idx = _ARCH.index(target_arch)
            target_system = _ARCH
        except ValueError:
            pass
    if target_system is None:
        raise ValueError(
            f"Unknown target architecture '{target_arch}' provided; please choose from"
            f" {_x86} for x86 systems, and {_ARM} for ARM systems."
        )
    return [target_system[idx] for idx in range(target_arch_idx + 1)]


def _pprint_config(config):
    for key in config:
        print(f"For function {key}:\n")
        spec = config[key]
        for section in spec:
            print(f"Showing section: {section}:\n")
            print(spec[section])
        print(f"{'':=^80}")


def get_config():
    definitions = glob.glob(join(DEFINITIONS_DIR, r"*.def"))
    config = {}
    for def_file_name in definitions:
        mode = None
        with open(def_file_name) as file:
            specification = {"SETUP": None, "BODY": None, "REMAINDER": None}
            section = ""
            for line in file:
                line = line.rstrip()
                if line in ("SETUP", "BODY", "REMAINDER"):
                    if mode is not None:
                        specification[mode] = section
                    section = ""
                    mode = line
                else:
                    section += line + "\n"
            specification[mode] = section
        function_name = basename(def_file_name)[:-4]
        config[function_name] = specification
    return config


def gen_from_config(config, target_arch):
    ARCHITECTURES = _make_architectures(target_arch)
    print(f"Generating the following SIMD targets: {ARCHITECTURES}...\n")

    file_template = dedent("""\
        #ifndef {1}_HPP
        #define {1}_HPP
        #include "utils.hpp"

        struct _{0}{{
        template <class Arch, typename Type>
        Type operator()(Arch, const Type* a, const Type* b, const std::size_t size);
        }};

        #define {1}_SETUP(ITER) \\
        {2}
        #define {1}_BODY(ITER) \\
        {3}
        template <class Arch, typename Type>
        Type _{0}::operator()(Arch, const Type* a, const Type* b, const std::size_t size){{
            using batch_type = xs::batch<Type, Arch>;
            MAKE_STD_VEC_LOOP({1}_SETUP, {1}_BODY, batch_type)

        {4}
        }}
        """)  # noqa

    target_specific_templates = {}
    for arch in ARCHITECTURES:
        target_specific_templates[arch] = """#include "{0}.hpp"\n"""
        file_template += "\n"
        file_template += f"// {arch.upper()}\n"
        for type in ("float", "double"):
            signature = f"template {type} _{{0}}::operator()<xs::{arch}, {type}>(xs::{arch}, const {type} *, const  {type} *, const std::size_t);\n"  # noqa
            target_specific_templates[arch] += signature
            file_template += "extern " + signature

    file_template += "#else\n#endif"
    for metric, spec in config.items():
        file_content = file_template.format(
            metric,
            metric.upper(),
            indent(spec["SETUP"], PY_TAB),
            indent(spec["BODY"], PY_TAB),
            indent(spec["REMAINDER"], PY_TAB),
        )
        file_path = join(GENERATED_DIR, f"{metric}.hpp")
        with open(file_path, "w") as file:
            file.write(file_content)

        for arch in ARCHITECTURES:
            file_path = join(GENERATED_DIR, f"{metric}_{arch}.cpp")
            with open(file_path, "w") as file:
                file.write(target_specific_templates[arch].format(metric))


def generate_code(target_arch):
    # TODO: First check to see whether any source files have been modified and
    # actually require to be regenerated, or an environment flag specifying
    # such has been set.
    Path(GENERATED_DIR).mkdir(parents=True, exist_ok=True)
    gen_from_config(get_config(), target_arch)
