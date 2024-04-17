import re
def cidToChar(cidx):
    return chr(int(re.findall(r'\(cid\:(\d+)\)',cidx)[0]) + 29)