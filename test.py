import re

s1 = "<: fufu : 1309144706726498388 > <: fufu : 1309144706726498388 > < : dame_nandayo : 1305728227779678258 >aaaaa<: dame _ nandayo : 1305728227779678258 >aaaa"
s2 = "これとかさ https://eng-entrance.com/linux_command_cp"

def remove_url(text):
    return re.sub(r'(https?|ftp)(:\/\/[\-\_\.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)','', text)

def conbine_matched_emoji_tag(match):
    emoji_alias_str = "".join(match.group(1).split())
    id_str = match.group(2)
    return fr'<:{emoji_alias_str}:{id_str}>'

def conbine_emoji_tag(text):
     return re.sub(r'<[ ]*?:([ 　\-\_\.!~*a-zA-Z0-9;\/?\@&=\+\$,%#]+):[ ]+?([0-9]+?)[ ]+?>', conbine_matched_emoji_tag, text)



print(conbine_emoji_tag(s1))
print(remove_url(s2))