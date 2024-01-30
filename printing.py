import colorama

colorama.init()


def printc(color, s, **kwargs):
    cc = eval(f"colorama.Fore.{color.upper()}")
    print(cc + s + colorama.Style.RESET_ALL, **kwargs)


def printf(file, s, **kwargs):
    with open(file, "a") as f:
        print(s, file=f, **kwargs)
