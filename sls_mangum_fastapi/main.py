from typing import List

from fastapi import FastAPI
from mangum import Mangum
from pydantic import BaseModel
from pynamodb.attributes import NumberAttribute, UnicodeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, KeysOnlyProjection
from pynamodb.models import Model

from config import AWS_REGION, DDB_HOST, DDB_TABLE

app = FastAPI()


# Request bodyを受けるためのクラス(FastAPI)
class Students(BaseModel):
    name: str

class ExamScore(BaseModel):
    subject: str
    student_name: str
    score: int


# DynamoDBとやりとりするクラス(PynamoDB)
class SubjectIndex(GlobalSecondaryIndex):
    """
    教科単位で成績を引く
    """
    class Meta:
        projection = KeysOnlyProjection()
        read_capacity_units = 1
        write_capacity_units = 1
    subject = UnicodeAttribute(hash_key=True)
    score = NumberAttribute(range_key=True)

class StudentsTable(Model):
    """
    生徒の成績を保持するテーブル
    """
    class Meta:
        table_name = DDB_TABLE
        region = AWS_REGION
        host = DDB_HOST

    name = UnicodeAttribute(hash_key=True)
    subject = UnicodeAttribute(range_key=True)
    score = NumberAttribute()
    # GSIs
    by_subject = SubjectIndex()


@app.get("/")
def hello():
    return {"Hello": "World"}

@app.get("/students")
def list_students():
    return {"students": ["Alice", "Bob", "Charlie"]}

handler = Mangum(app, False)


def init_ddb_local():
    if StudentsTable.Meta.host and not StudentsTable.exists():
        print('creating a table...')
        StudentsTable.create_table(
            read_capacity_units=1,
            write_capacity_units=1,
            wait=True
        )
        print('Done.')
