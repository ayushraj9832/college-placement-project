import getpass
import sys

from werkzeug.security import check_password_hash, generate_password_hash


def main():
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = getpass.getpass("Password to hash: ")
        confirm = getpass.getpass("Confirm password : ")
        if password != confirm:
            print("Passwords do not match.")
            return 1

    if len(password) < 6:
        print("Use at least 6 characters.")
        return 1

    password_hash = generate_password_hash(password)
    if not check_password_hash(password_hash, password):
        print("Hash verification failed.")
        return 1

    print()
    print(password_hash)
    print()
    print("Verified OK. Paste the line above into the Password_Hash column.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
