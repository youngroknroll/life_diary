from ninja import Schema


class CategoryOut(Schema):
    id: int
    name: str
    slug: str
    description: str
    color: str
    display_order: int


class CategoryListOut(Schema):
    success: bool
    message: str
    categories: list[CategoryOut]


class TagUsageOut(Schema):
    id: int
    name: str
    color: str
    category_id: int
    can_edit: bool
    can_delete: bool
    block_count: int
    total_hours: float


class TagListOut(Schema):
    success: bool
    message: str
    tags: list[TagUsageOut]


class TagIn(Schema):
    name: str = ""
    color: str = ""
    category_id: int | None = None


class TagOut(Schema):
    id: int
    name: str
    color: str
    category_id: int


class TagMutationOut(Schema):
    success: bool
    message: str
    tag: TagOut
