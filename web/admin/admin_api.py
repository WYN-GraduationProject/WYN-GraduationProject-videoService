from fastapi import APIRouter, Depends
from utils.model.post import PostModel, PostSchema
from infrastructure_layer.admin.admin_model import PostManager
from typing import List

router = APIRouter(
    prefix="/api/post",
    tags=["post"],
    responses={404: {"description": "Not found"}},
)


def get_post_manager():
    return PostManager()


@router.post("/posts/")
def create_post(post: PostSchema, post_manager: PostManager = Depends(get_post_manager)):
    post = PostModel(**post.dict())
    post_manager.add_post(post)
    return post


@router.get("/posts/")
def read_posts(post_manager: PostManager = Depends(get_post_manager)):
    return post_manager.get_all_posts()
