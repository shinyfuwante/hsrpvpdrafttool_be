from dataclasses import dataclass

@dataclass
class Pick:
    name: str
    eidolon: int
    stars: int
    lightcone: id
    lightcone_name: str
    superimposition: int
    
    
@dataclass
class Ban:
    name: str
    stars: int