import sys

from zoom_helper import App


def main():
    app = App()
    if "--admin" in sys.argv:
        app.after(300, app._open_admin)
    app.mainloop()


if __name__ == "__main__":
    main()
