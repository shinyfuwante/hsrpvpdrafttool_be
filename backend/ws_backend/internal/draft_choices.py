from dataclasses import dataclass

@dataclass
class Pick:
    name: str
    eidolon: int
    light_cone: str
    superimposition: int
    index: int
    
    
    
@dataclass
class Ban:
    name: str
    stars: int