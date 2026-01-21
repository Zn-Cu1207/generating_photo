from fastapi import routing, Depends
from ..schema.prompt import PromptRequest
from ..db.models import Record
from ..db.session import get_session



router = routing.APIRoute()


@router.post('/api/pic')
def create_prompt_to_pic(req: PromptRequest, sess: Depends[get_session]):
    record = Record(prompt=req.prompt)
    sess.add(record)
    sess.commit()
    
    return {}

def query_prompts(page: int, size: int, sess: Depends[get_session]) -> list[Record]:
    records = sess.select(Record).all()

    records[0]
    records[1]
    records[2]

    return records


def update_prompt(id_: int, sess: Depends[get_session]) -> list[Record]:
    record = sess.select(Record).where(Record.id == id_).one()

    record.prompt = 'xxxx'
    sess.add(record)
    sess.commit()

    return record

