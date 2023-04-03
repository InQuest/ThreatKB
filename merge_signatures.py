import sys
import uuid
import re
from plyara import Plyara
import argparse

# Appears that Ply needs to read the source, so disable bytecode.
sys.dont_write_bytecode


def get_strings_and_conditions(rule):
    segment_headers = \
        {
            "strings": "^\s*strings:\s*\r?\n?",
            "condition": "^\s*condition:\s*\r?\n?",
        }
    segments = \
        {
            "strings": [],
            "condition": [],
        }
    SEGMENT = None
    for line in rule.splitlines():
        segment_change = False
        for header, rx in list(segment_headers.items()):
            if re.match(rx, line):
                SEGMENT = header
                segment_change = True
        if SEGMENT and not segment_change:
            segments[SEGMENT].append(line)

    if segments.get("strings", None):
        segments["strings"][-1] = segments["strings"][-1].rstrip(" }") if not "=" in segments["strings"][-1] else \
            segments["strings"][-1]

    if segments.get("condition", None):
        segments["condition"][-1] = segments["condition"][-1].rstrip().rstrip(" }\n\t")

    return "\n".join(segments["strings"]) if segments.get("strings", None) else "", "\n".join(
        [segment for segment in segments["condition"] if segment.strip(" }")])


def parse_yara_rules_text(text):
    return Plyara().parse_string(text)


def parse_yara_rules_file(filename):
    return parse_yara_rules_text(open(filename, "r").read())


def get_imports_from_string(imports_string):
    if not imports_string:
        return ""
    return "\n".join([imp.strip() for imp in
                      set(re.findall(r'^import[\t\s]+\"[A-Za-z0-9_]+\"[\t\s]*$', imports_string, re.MULTILINE))])


def extract_yara_rules_text(text):
    text = text.strip()
    imports = get_imports_from_string(text)
    split_regex = "\n[\t\s]*\}[\s\t]*(rule[\t\s][^\r\n]+(?:\{|[\r\n][\r\n\s\t]*\{))"
    parse_regex = r"^[\t\s]*rule[\t\s][^\r\n]+(?:\{|[\r\n][\r\n\s\t]*\{).*?condition:.*?\r?\n?[\t\s]*\}[\s\t]*(?:$|\r?\n)"

    yara_rules = re.sub(split_regex, "\n}\n\\1", text, re.MULTILINE | re.DOTALL)
    yara_rules = re.compile(parse_regex, re.MULTILINE | re.DOTALL).findall(yara_rules)
    extracted = []
    for yara_rule_original in yara_rules:
        try:
            parsed_rule = parse_yara_rules_text(yara_rule_original.strip())[0]

            strings, condition = get_strings_and_conditions(yara_rule_original)
            extracted.append(
                {"parsed_rule": parsed_rule, "strings": strings, "condition": condition, "imports": imports})
        except Exception as e:
            pass

    return extracted


def merge_signatures(signatures):
    if not signatures:
        return None

    rules = extract_yara_rules_text(signatures)
    rule_name = f"Merged_Rule_{str(uuid.uuid4())[:8]}"
    description = f"\"Merger of {', '.join([rule['parsed_rule']['rule_name'] for rule in rules])}\""
    strings = ""
    condition = ""
    imports = ""
    r = 1
    for rule in rules:
        old_new = {}
        current_strings = []
        postfix = f"r{r}"
        for s in rule['parsed_rule']['strings']:
            old_name = s['name'].strip()
            if old_name.startswith('$'):
                name = f"${s['name'].strip()[1:]}_{postfix}"
            else:
                name = f"{s['name'].strip()}_{postfix}"

            if s['value'].startswith("{") or s['value'].startswith("/"):
                value = s['value'].strip()
            else:
                value = f"\"{s['value'].strip()}\""

            old_new[old_name] = name
            modifier = ' '.join(s.get('modifiers', []))
            current_strings.append(
                f"{name} = {value} {modifier}"
            )
        strings += '\n\t\t' + '\n\t\t'.join(current_strings)
        this_condition = rule['condition'].strip()
        for old, new in old_new.items():
            this_condition = this_condition.replace(old, new)
        condition += f"(\n\t{this_condition}\n\t)\n\tor\n\t"
        imports += rule['imports'] + "\n" if not rule['imports'] in imports else ""
        r += 1

    condition = condition.rstrip("\n\tor\n\t")
    full_rule = f"""
    {imports}

    rule {rule_name}
    {{
        meta:
            description = {description}
        strings:{strings}
        condition:
            {condition}
    }}
    """

    return full_rule.strip(" ").strip()


def main(args):
    parser = argparse.ArgumentParser(
        description="merge_signatures.py is a cli tool and library for intelligently merging yara signatures."
    )

    # Define accepted arguments and metadata.
    parser.add_argument('--file',
                        action='store',
                        type=str,
                        dest='file',
                        required=False)

    args = parser.parse_args()
    text = open(args.file, "r").read() if args.file else sys.stdin.read()
    print(merge_signatures(text))
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv)
