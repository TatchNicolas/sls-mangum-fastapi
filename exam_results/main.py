from os import environ
from typing import List

from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel
from pynamodb.attributes import NumberAttribute, UnicodeAttribute
from pynamodb.indexes import GlobalSecondaryIndex, KeysOnlyProjection
from pynamodb.models import Model



DDB_HOST = environ.get('DDB_HOST')
DDB_TABLE = environ['DDB_TABLE']
AWS_REGION = environ['AWS_REGION']

app = FastAPI()

# ---------------------------
# FastAPIで扱う
# ---------------------------

class ExamResult(BaseModel):
    name: str
    subject: str
    score: int

class ExamResultList(BaseModel):
    exam_results: List[ExamResult]

# ---------------------------
# PynamoDBで扱う
# ---------------------------
class SubjectIndex(GlobalSecondaryIndex):
    """
    教科単位で成績を引くGSI
    """
    class Meta:
        projection = KeysOnlyProjection()
        read_capacity_units = 1
        write_capacity_units = 1
    subject = UnicodeAttribute(hash_key=True)
    score = NumberAttribute(range_key=True)

class ExamResultsTable(Model):
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
    # GSI
    by_subject = SubjectIndex()


# ---------------------------
# パスごとの処理を記述
# ---------------------------

@app.post("/scores", response_model=ExamResult)
def save_score(exam_result: ExamResult):
    """
    試験の成績を保存する
    """
    new_score = ExamResultsTable(
        exam_result.name,
        subject=exam_result.subject,
        score=exam_result.score,
    )
    new_score.save()
    return {
        "student": new_score.name,
        "subject": new_score.subject,
        "score": new_score.score,
    }

@app.get("/scores")
def get_score(student: str=None, subject: str=None):
    """
    試験の成績を問い合わせる
    """

    if (student and subject) or not (student or subject):
        raise HTTPException(
            status_code=400,
            detail="Expects exactly one of the following query parameters: student, subject"
        )

    if student:
        return [
            {
                "name": score.name,
                "subject": score.subject,
                "score": score.score,
            } for score in ExamResultsTable.query(student)
        ]

    if subject:
        return [
            {
                "name": score.name,
                "subject": score.subject,
                "score": score.score,
            } for score in SubjectIndex.query(subject)
        ]

    raise HTTPException(
            status_code=400,
            detail="Expects exactly one of the following query parameters: student, subject"
    )


handler = Mangum(app, False)

# ---------------------------
# ローカル環境の初期化用
# docker-compose exec 
# ---------------------------

def init_ddb_local():
    if ExamResultsTable.Meta.host and not ExamResultsTable.exists():
        print('creating a table...')
        ExamResultsTable.create_table(
            read_capacity_units=1,
            write_capacity_units=1,
            wait=True
        )
        print('Done.')
