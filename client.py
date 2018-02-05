# create client data structure
class Client:
    def __init__(self, name, id): 
        self._name = name
        self._id = id
    
    @property
    def name(self):
        return self._name
    
    @property
    def id(self):
        return self._id

    def __hash__(self):
        return hash((self.name, self.id))
    
    def __eq__(self, other):
        return (self.name, self.id) == (other.name, other.id)