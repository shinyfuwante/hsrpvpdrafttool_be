from dataclasses import dataclass

@dataclass
class Pick:
    id: int
    name: str
    eidolon: int
    stars: int
    lightcone: id
    lightcone_name: str
    superimposition: int
    
    
@dataclass
class Ban:
    id: int
    name: str
    stars: int