import argparse
from getpass import getpass

from sqlalchemy import delete

from app import __version__
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import session_scope
from app.models.user_session import UserSession
from app.repositories.users import get_user_by_username
from app.services.demo_seed import seed_demo_data


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


def seed_demo(confirm: bool) -> int:
    if get_settings().app_env.lower() == "production":
        print("生产环境禁止写入演示数据，请使用独立的本地或演示数据库")
        return 1
    if not confirm:
        print("该命令会重建带有 [演示] 前缀的数据；确认后请添加 --confirm")
        return 1
    with session_scope() as session:
        summary = seed_demo_data(session)
    print(
        "演示数据已生成："
        f"设备 {summary['devices']} 台，指标 {summary['metrics']} 条，告警 {summary['alerts']} 条"
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="NodeWatch 管理命令")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    password_parser = subparsers.add_parser("change-password", help="修改用户密码")
    password_parser.add_argument("username")
    seed_parser = subparsers.add_parser("seed-demo", help="在非生产数据库生成可重复的演示数据")
    seed_parser.add_argument("--confirm", action="store_true", help="确认重建演示数据")
    args = parser.parse_args()
    if args.command == "change-password":
        raise SystemExit(change_password(args.username))
    if args.command == "seed-demo":
        raise SystemExit(seed_demo(args.confirm))


if __name__ == "__main__":
    main()
