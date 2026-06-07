from fastapi import APIRouter, HTTPException, Path, status, Query, Depends
from auth import CurrentUser
from database import get_db
from models.task import TaskStatus, Task
from schemas import TaskCreate, TaskResponse, TaskUpdate
from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("", response_model=list[TaskResponse])
async def get_all_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0, 
    limit: Annotated[int, Query(le=100)] = 10,
    ):
    result = await db.execute(
        select(Task).
        options(selectinload(Task.user)).
        limit(limit).
        offset(skip)
        )
    tasks = result.scalars().all()

    return tasks


@router.get("/{item_id}", response_model=TaskResponse)
async def get_item(item_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
   result = await db.execute(
       select(Task).
       options(selectinload(Task.user)).
       where(Task.id == item_id)
   )
   task = result.scalars().first()
   
   if task:
       return task
   else: raise HTTPException(
       status_code=status.HTTP_404_NOT_FOUND,
       detail="Ain't, this post ain't real"
   )

@router.get("/status/{status_type}", response_model=list[TaskResponse])
async def get_items_with_status(
    status_type: TaskStatus,
    db: Annotated[AsyncSession, Depends(get_db)]
    ):
    result = await db.execute(
       select(Task).
       options(selectinload(Task.user)).
       where(Task.status == status_type)
    )
    tasks = result.scalars().all()
    
    if tasks:
        return tasks
    else: raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Ain't, these post with this status ain't real"
    )

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate, 
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser
    ):
    post = Task(
        title = task.title,
        content = task.content,
        status = task.status,
        due_date = task.due_date,
        user_id = current_user.id
    )
    db.add(post)
    await db.commit()
    await db.refresh(post, attribute_names=["user"])
    return post

@router.patch("/{item_id}", response_model=TaskResponse)
async def partial_update(
    item_id: Annotated[int, Path(title="The ID of task to modified", ge=0, le=1000)],
    db: Annotated[AsyncSession, Depends(get_db)],
    task: TaskUpdate,
    current_user: CurrentUser
):
    result = await db.execute(
        select(Task).
        where(Task.id == item_id)
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ain't find post to modify"
        )
    
    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this post"
        )
    
    updated_data = task.model_dump(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item, attribute_names=["user"])
    return item

@router.put("/{item_id}", response_model=TaskResponse)
async def full_update(
    item_id: Annotated[int, Path(title="The ID of task to modified", ge=0, le=1000)],
    db: Annotated[AsyncSession, Depends(get_db)],
    task: TaskCreate,
    current_user: CurrentUser
):
    result = await db.execute(
        select(Task).
        where(Task.id == item_id)
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ain't find post to modify"
        )
    
    if item.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this post"
        )
    
    for key, value in task.model_dump().items():
        setattr(item, key, value)

    await db.commit()
    await db.refresh(item, attribute_names=["user"])

    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    item_id: Annotated[int, Path(title="The ID of task to modified", ge=0, le=1000)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser
):
    result = await db.execute(
        select(Task).
        where(Task.id == item_id)
    )
    task = result.scalars().first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ain't find post to delete"
    ) 

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )

    await db.delete(task)
    await db.commit()