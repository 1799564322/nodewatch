import argparse
from getpass import getpass

from sqlalchemy import delete

from app.core.security import hash_password
from app.db.session import session_scope
from app.models.user_session import UserSession
from app.repositories.users import get_user_by_username


def change_password(username: str) -> int:
    password = getpass("新密码：")
    confirmation = getpass("再次输入新密码：")
    if password != confirmation:
        print("两次输入的密码不一致")
        return 1
    if len(password) < 12:
        print("密码不能少于 12 个字符")
        return 1
    with session_scope() as session:
        user = get_user_by_username(session, username)
        if user is None:
            print(f"用户不存在：{username}")
            return 1
        user.password_hash = hash_password(password)
        session.execute(delete(UserSession).where(UserSession.user_id == user.id))
    print(f"密码已更新，旧会话已撤销：{username}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="NodeWatch 管理命令")
    subparsers = parser.add_subparsers(dest="command", required=True)
    password_parser = subparsers.add_parser("change-password", help="修改用户密码")
    password_parser.add_argument("username")
    args = parser.parse_args()
    if args.command == "change-password":
        raise SystemExit(change_password(args.username))


if __name__ == "__main__":
    main()
