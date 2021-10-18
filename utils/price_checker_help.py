def is_digit(string):
    if string.isdigit():
       return True
    else:
        try:
            int(string)
            return True
        except ValueError:
            return False

def check_link_valid(link):
    "https://lolz.guru/market/20831991/"

    spl = link.split('/')
    print(spl)
    # print(spl)
    if len(spl) != 6:
        # print(len(spl))
        # print('0')
        return False
    if spl[0] != 'https:':
        # print('1')
        return False
    if spl[2] != 'lolz.guru':
        # print('2')
        return False
    if spl[3] != 'market':
        # print('3')
        return False
    if not is_digit(spl[4]):
        # print('4')
        return False
    if spl[5] != '':
        # print(spl[5])
        # print('5')
        return False
    return True