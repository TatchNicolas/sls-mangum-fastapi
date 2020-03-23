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

class StudentsModel(Model):
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


    @classmethod
    def init_ddb_local(cls):
        """
        docker-composeでローカル開発するときにDBを初期化する
        環境変数としてDDB_HOSTを渡して、かつ接続先DDBにテーブルがない場合に動く
        AWS上のテーブルはserverless.ymlの中でCloudFormationとして定義している
        """
        if cls.Meta.host and not cls.exists():
            print(f'creating a table {cls.Meta.table_name} for {cls.Meta.host}')
            cls.create_table(read_capacity_units=1, write_capacity_units=1, wait=True)


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/students")
def list_students():
    return {"students": ["Alice", "Bob", "Charlie"]}

handler = Mangum(app, False)
