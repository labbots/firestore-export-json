import sys
from converter import command

def main():
    args = sys.argv[1:]
    command.main(args=args)

if __name__ == '__main__':
    main()