import time
from capture import capture
from recognize import recognize
from click import click

def extract():
    click(2380, 1250)

def abandon():
    click(1792, 1476)
    time.sleep(0.5)
    click(1492, 976)
    time.sleep(0.5)

def main():
    while True:
        img = capture(False)
        res = recognize(img)
        non_zero=0
        five_count=0
        for ch in res:
            if ch.isdigit():
                if ch=='5':
                    five_count+=1
                    continue
                if ch!='0':
                    non_zero+=1
        if five_count==4:
            break
        if non_zero>=2:
            abandon()
        extract()
        time.sleep(1)
    return

if __name__ == "__main__":
    main()
