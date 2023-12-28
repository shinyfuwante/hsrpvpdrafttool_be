from dataclasses import dataclass

@dataclass
class Pick:
    name: str
    eidolon: int = 0
    lightcone_name: str = ""
    superimposition: int = 1
    
    
@dataclass
class Ban:
    name: str
    stars: int