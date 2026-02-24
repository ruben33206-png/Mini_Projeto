from fastapi import FastAPI, HTTPException, Depends
import uvicorn
from database import engine, SessionLocal
from models import Base, User, Game, Quest, UserQuest
from schemas import (
    UserCreate,
    UserOut,
    UserLogin,
    QuestOut,
    CompletedQuest,
    CompletedGameGroup,
    CompletedQuestsResponse,
    ChangeUsername, 
    ChangeEmail, 
    ChangePassword,
    DeleteUserRequest
)
from sqlalchemy.orm import Session
import uuid
from utils import add_xp_and_update_level
from datetime import datetime

app = FastAPI()
Base.metadata.create_all(bind=engine)

@app.get("/")
def read_root():
    return {"message": "API funcionando"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/registro")
def registrar_usuario(user: UserCreate, db: Session = Depends(get_db)):
    user_exist = db.query(User).filter(User.email == user.email).first()
    if user_exist:
        raise HTTPException(status_code=400, detail="Email já está registrado")

    novo_user = User(
        userid=str(uuid.uuid4()), 
        username=user.username,
        email=user.email,
        passencrypt=user.password, 
        currentxp=0,
        currentlvl=0
    )

    db.add(novo_user)
    db.commit()
    db.refresh(novo_user)

    return {"message": "Usuário registrado com sucesso", "userid": novo_user.userid}

@app.get("/users", response_model=list[UserOut])
def listar_users(db: Session = Depends(get_db)):
    users = db.query(User).filter(User.userid != "main").all()
    return users

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Email/Password Incorretos")

    if db_user.passencrypt != user.password:
        raise HTTPException(status_code=400, detail="Email/Password Incorretos")
    
    return {
        "message": "Login efetuado com sucesso",
        "userid": db_user.userid,
        "username": db_user.username,
        "email": db_user.email,
        "currentxp": db_user.currentxp,
        "currentlvl": db_user.currentlvl
    }

@app.get("/games")
def listar_games(db: Session = Depends(get_db)):
    games = db.query(Game).all()
    return [
        {
            "gameid": g.gameid,
            "gamename": g.gamename
        }
        for g in games
    ]

@app.get("/quests/disponiveis/{userid}", response_model=list[QuestOut])
def quests_disponiveis(userid: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userid == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User não encontrado")
    completed_ids = db.query(UserQuest.questid).filter(UserQuest.userid == userid).all()
    completed_ids = [q[0] for q in completed_ids]
    quests = db.query(Quest).filter(Quest.questid.not_in(completed_ids)).all()
    result = []
    for q in quests:
        result.append({
            "questid": q.questid,
            "questname": q.questname,
            "questdescription": q.questdescription,
            "requirements": q.requirements,
            "howtodoit": q.howtodoit,
            "rewards": q.rewards,
            "isdaily": q.isdaily,
            "gameid": q.gameid,
            "gamename": q.game.gamename
        })

    return result





XP_REWARD = 10

@app.post("/quests/check/{userid}/{questid}")
def check_quest(userid: str, questid: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userid == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User não encontrado")

    quest = db.query(Quest).filter(Quest.questid == questid).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest não encontrada")

    already = db.query(UserQuest).filter(
        UserQuest.userid == userid,
        UserQuest.questid == questid
    ).first()

    if already:
        raise HTTPException(status_code=400, detail="Quest já foi completada")

    user_quest = UserQuest(
        userid=userid,
        questid=questid,
        gameid=1,
        completedwhen=str(datetime.now())
    )

    db.add(user_quest)

    add_xp_and_update_level(user, XP_REWARD)

    db.commit()
    db.refresh(user)

    return {
        "message": "Quest marcada como concluída",
        "xp_ganho": XP_REWARD,
        "currentxp": user.currentxp,
        "currentlvl": user.currentlvl
    }

@app.get("/quests/completas/{userid}", response_model=CompletedQuestsResponse)
def quests_completas(userid: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userid == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User não encontrado")

    completed = db.query(UserQuest).filter(UserQuest.userid == userid).all()

    games_dict = {}

    for uq in completed:
        game = uq.game
        quest = uq.quest

        if game.gameid not in games_dict:
            games_dict[game.gameid] = {
                "gameid": game.gameid,
                "gamename": game.gamename,
                "quests": []
            }

        games_dict[game.gameid]["quests"].append({
            "questid": quest.questid,
            "questname": quest.questname,
            "questdescription": quest.questdescription,
            "rewards": quest.rewards
        })

    games_list = list(games_dict.values())

    return {
        "userid": userid,
        "games": games_list
    }

@app.put("/changeuser/{userid}")
def change_username(userid: str, data: ChangeUsername, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userid == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User não encontrado")

    user.username = data.new_username
    db.commit()
    db.refresh(user)

    return {"message": "Username atualizado com sucesso", "new_username": user.username}

@app.put("/changemail/{userid}")
def change_email(userid: str, data: ChangeEmail, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userid == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User não encontrado")

    email_exists = db.query(User).filter(User.email == data.new_email).first()
    if email_exists:
        raise HTTPException(status_code=400, detail="Email já está em uso")

    user.email = data.new_email
    db.commit()
    db.refresh(user)

    return {"message": "Email atualizado com sucesso", "new_email": user.email}

@app.put("/changepass/{userid}")
def change_password(userid: str, data: ChangePassword, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userid == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User não encontrado")

    user.passencrypt = data.new_password
    db.commit()
    db.refresh(user)

    return {"message": "Password atualizada com sucesso"}

@app.delete("/deleteuser/{userid}")
def delete_user(userid: str, data: DeleteUserRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.userid == userid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User não encontrado")

    if user.passencrypt != data.password:
        raise HTTPException(status_code=401, detail="Password incorreta")

    db.query(UserQuest).filter(UserQuest.userid == userid).delete()

    db.delete(user)
    db.commit()

    return {"message": "Utilizador eliminado com sucesso"}
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
