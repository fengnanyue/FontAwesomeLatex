# This script is designed to generate LaTeX wrapper (fontawesome.sty)
#  for Font Awesome ver. 4.1 by Dave Gandy (http://fontawesome.io/)
#
# Original wrapper created by Xavier Danaux for Font Awesome ver. 3.1.1
#  (http://www.ctan.org/tex-archive/fonts/fontawesome)
#
# Author: Nazar Gerasymchuk, troyan3 at gmail dot com
#  (https://github.com/troyane/FontAwesomeLatex)

__author__ = 'Nazar Gerasymchk, troyan3 at gmail dot com'

import tinycss
import re
import subprocess

# constants
path_to_css = "input/fontawesome_reduced.css"
path_to_backward_cap = "input/backward_cap.txt"
path_to_template = "input/template.sty"
path_to_output_file = "output/fontawesome.sty"
# icon-specific commands (in output file)
latex_pattern = r'\expandafter\def\csname faicon@%(csname)s\endcsname {\symbol{%(hex)s}} \def%(icon_name)s {{\FA\csname faicon@%(csname)s\endcsname}}'
# aliases (in output file)
latex_aliases_pattern = r'\expandafter\def\csname faicon@%(alias_name)s\endcsname {%(primary)s} \def%(alias_icon)s {%(primary_icon)s}'

# regex to catch hex number
fa_hex = re.compile(r'(\\)(f[0-9a-fA-F]+)')

#regex to catch backward capability string:
back_cap_pattern = re.compile(r'\*\s+`(\S+)`\s+->\s+`(\S+)`(.*)[,.](\s+)?')


def get_current_date_time():
    """
    Returns current date and time
    """
    import datetime
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M")


def get_git_info():
    """
    Executes command 'git describe --long --dirty --tags' and returns result
    """
    return subprocess.check_output(['git', 'describe', '--long', '--dirty', '--tags'])


def get_machine_info():
    """
    Executes command 'uname -a' and returns result
    """
    return subprocess.check_output(['uname', '-a'])


def match_back_cap_line(line):
    """
    Check weather line matches back_cap_pattern (ex. * `bar-chart` -> `bar-chart-o` (info),) and returns it in (old, new, comment)
    Otherwise returns none
    """
    matches = back_cap_pattern.search(line)
    if matches:
        old = matches.groups()[0]
        new = matches.groups()[1]
        comment = matches.groups()[2]
        return [old, new, comment]
    else:
        print "Wrong input: ", line
        return None


def to_latex_hex(hex_str):
    """
    Check weather hex_str matches hex number pattern (ex. \f000) and returns it in format "F000.
    Otherwise returns None
    """
    matches = fa_hex.search(hex_str)
    if matches:
        # we have correct FA hex
        new_hex = '"' + str(matches.groups()[1]).upper()
        return new_hex
    else:
        print "Wrong input: ", hex_str
        return None


def to_csnames(name):
    """
    name is icon name from CSS (ex. fa-search-plus), returns reformated name pair (ex. (search-plus, SearchPlus))
    """
    # hyphen_pos = name.find('-')
    if name.lower().startswith("fa-"):
        csname = name[3:]
    else:
        csname = name
    icon_name = r'\fa' + ''.join(w.title() for w in re.split(r'-', csname))

    return csname, icon_name


def main():
    cur_date = get_current_date_time()
    machine = get_machine_info().strip()
    git_info = get_git_info().strip()

    print "Started (" + git_info + "), " + cur_date + "\n\tat " + machine

    parser = tinycss.make_parser('page3')

    print "Parsing CSS file: ", path_to_css
    stylesheet = parser.parse_stylesheet_file(path_to_css)

    # hex_dict = dict of hex:
    #    hex => [icon0, icon1, ..., iconN],
    # where icon0 - primary; icon1, ..., iconN - aliases for icon0
    # where iconI - tuple of csname and icon_name
    hex_dict = dict()

    for rule in stylesheet.rules:
        sym_code = rule.declarations[0].value[0]._as_css
        hex = to_latex_hex(sym_code)
        if hex is None:
            print "ERROR: Wrong hex value in CSS: ", sym_code, ". Ignoring this icon. "
            continue
        icons = []
        for sel in rule.selector:
            if str(sel.value).startswith("fa-"):
                csname, icon_name = to_csnames(sel.value)
                # print csname, icon_name
                icons.append((csname, icon_name))
        if hex not in hex_dict:
            hex_dict[hex] = icons

    count_sumary = 0
    count_aliases = 0

    list_of_icons = ""
    list_of_aliases = ""

    sorted_keys = sorted(hex_dict.keys())
    for key in sorted_keys:
        val = hex_dict[key]
        # primary
        primary = val[0]
        pattern_dict = {'csname': primary[0],
                        'hex': key,
                        'icon_name': primary[1]}
        prep_latex = latex_pattern % pattern_dict
        count_sumary += 1
        list_of_icons += "\n" + prep_latex

        if len(val) > 1:
            # have aliases
            aliases = []
            for i in range(1, len(val)):
                # hold each alias except first, bc it is primary
                pattern_dict = {'alias_name': val[i][0],
                                'primary': primary[1],
                                'alias_icon': val[i][1],
                                'primary_icon': primary[1]}
                prep_alias = latex_aliases_pattern % pattern_dict
                aliases.append(val[i][1])
                list_of_aliases += "\n" + prep_alias
                count_sumary += 1
                count_aliases += 1

            # append information about aliases
            list_of_icons += " % has aliases: " + ", ".join(aliases)

            # make groups of ten records in aliases
            if count_aliases % 10 == 0:
                list_of_aliases += "\n"

        # make groups of ten records in primary icons
        if count_sumary % 10 == 0:
            list_of_icons += "\n"

    print "Reading template: ", path_to_template
    f_template = open(path_to_template, "r")
    template = f_template.read()
    f_template.close()

    print "Reading backward capability icons: ", path_to_backward_cap
    list_of_capability_aliases = ""
    f_back = open(path_to_backward_cap, "r")
    count_back_cap = 0
    for line in f_back:
        pair = match_back_cap_line(line)
        if pair is not None:
            cur_comment = pair[2]
            old_alias = to_csnames(pair[0])
            new_alias = to_csnames(pair[1])
            pattern_dict = {'alias_name': old_alias[0],
                            'primary': new_alias[1],
                            'alias_icon': old_alias[1],
                            'primary_icon': new_alias[1]}
            prep_back_alias = latex_aliases_pattern % pattern_dict
            list_of_capability_aliases += "\n" + prep_back_alias
            if cur_comment != "":
                list_of_capability_aliases += " % " + cur_comment
            count_back_cap += 1
            # make groups of ten records in capability aliases
            if count_back_cap % 10 == 0:
                list_of_capability_aliases += "\n"
    f_back.close()

    print "Summary: \n\tcount of icons: " + str(count_sumary) + " (with " + str(count_aliases) + " aliaces)" + \
          "\n\tUnique icons: " + str(count_sumary - count_aliases) + \
          "\n\tBackward capability icons: " + str(count_back_cap)


    print "Writing output to: ", path_to_output_file
    f_result = open(path_to_output_file, "w")

    result_pattern = {'date_generation': cur_date,
                      'machine': machine,
                      'git_info': git_info,
                      'listOfIcons': list_of_icons,
                      'listOfAliases': list_of_aliases,
                      'listOfCapabilityAliases': list_of_capability_aliases}
    output = template % result_pattern
    f_result.write(output)
    f_result.close()
    print "Done. See output folder."

if __name__ == "__main__":
    main()
