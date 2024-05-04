import configparser

from utils.tools.NacosManager import _NACOS_MANAGER
from utils.tools.SqlManager import SqlManager
from utils.model.post import PostModel

config = _NACOS_MANAGER.get_config_utils("WYNbysj").get_config()
config_parser = configparser.ConfigParser()
config_parser.read_string(f"[DEFAULT]\n{config}")

# 现在可以像使用字典一样访问配置值
mysql_host = config_parser["DEFAULT"]["MYSQL_HOST"]
mysql_user = config_parser["DEFAULT"]["MYSQL_USER"]
mysql_password = config_parser["DEFAULT"]["MYSQL_PASSWORD"]
mysql_database = config_parser["DEFAULT"]["MYSQL_DATABASE"]

sql_manager = SqlManager(mysql_host, mysql_user, mysql_password, mysql_database)


class PostManager:
    def __init__(self, _sql_manager: SqlManager = sql_manager):
        self.sql_manager = _sql_manager
        self.sql_manager.create_engine().create_table()
        self.session = _sql_manager.get_session()

    def add_post(self, post: PostModel):
        self.session.add(post)
        self.session.commit()

    def get_post(self, post_id: int):
        return self.session.query(PostModel).filter(PostModel.id == post_id).first()

    def get_all_posts(self):
        return self.session.query(PostModel).all()

    def update_post(self, post_id: int, new_content: str):
        post = self.get_post(post_id)
        post.content = new_content
        self.session.commit()

    def delete_post(self, post_id: int):
        post = self.get_post(post_id)
        self.session.delete(post)
        self.session.commit()
