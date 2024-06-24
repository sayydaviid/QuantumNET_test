import networkx as nx
from quantumnet.components import Host
from quantumnet.objects import Logger, Epr
from random import uniform


class NetworkLayer:
    def __init__(self, network, link_layer, physical_layer):
        """
        Inicializa a camada de rede.
        
        args:
            network : Network : Rede.
            link_layer : LinkLayer : Camada de enlace.
        """
        self._network = network
        self._link_layer = link_layer
        self._physical_layer = physical_layer
        self.logger = Logger.get_instance()


    def __str__(self):
        """ Retorna a representação em string da camada de rede. 
        
        returns:
            str : Representação em string da camada de rede."""
        return f'Network Layer'
    
    def verify_channels(self):
        """
        Verifica se todos os canais possuem pelo menos um par EPR.
        """
        for edge in self._network.graph.edges:
            if len(self._network.get_eprs_from_edge(edge[0], edge[1])) == 0:
                self.logger.log(f'No EPR pairs between {edge[0]} and {edge[1]}')
                return False
        self.logger.log(f'Tem par nesse negocio')
        return True
    

    def verify_nodes(self):
        """
        Verifica se todos os nós possuem pelo menos 2 qubits.
        
        returns:
            bool : True se todos os nós possuem pelo menos 2 qubits, False caso contrário.
        """
        for node in self._network.graph.nodes:
            host = self._network.get_host(node)
            if len(host.memory) < 2:
                self.logger.log(f'Node {node} does not have at least 2 qubits')
                return False
        self.logger.log('Todos os nós possuem pelo menos 2 qubits')
        return True

    def short_route_valid(self, Alice: int, Bob: int):
        """
        Escolhe a melhor rota entre dois hosts com critérios adicionais.
        
        args:
            Alice (int): ID do host de origem.
            Bob (int): ID do host de destino.
            
        returns:
            list or None: Lista com a melhor rota entre os hosts ou None se não houver rota válida.
        """
        try:
            # Calcula todas as menores rotas entre Alice e Bob
            all_shortest_paths = list(nx.all_shortest_paths(self._network.graph, Alice, Bob))
        except nx.NetworkXNoPath:
            self.logger.log(f'Sem rota encontrada entre {Alice} e {Bob}')
            return None
        
        # Verifica cada rota encontrada
        for path in all_shortest_paths:
            valid_path = True
            # Verifica cada canal (aresta) na rota
            for i in range(len(path) - 1):
                node = path[i]
                next_node = path[i + 1]
                # Verifica se o canal possui pelo menos 1 par EPR
                if len(self._network.get_eprs_from_edge(node, next_node)) < 1:
                    self.logger.log(f'Sem pares Eprs entre {node} e {next_node} na rota {path}')
                    valid_path = False
                    break
                # Verifica se o nó possui pelo menos 2 qubits
                host = self._network.get_host(node)
                if len(host.memory) < 2:
                    self.logger.log(f'Nó {node} não tem pelo menos 2 qubits na rota {path}')
                    valid_path = False
                    break
            
            # Se encontrou uma rota válida, retorna essa rota
            if valid_path:
                self.logger.log(f'Rota válida encontrada: {path}')
                return path
        
        # Se não encontrou nenhuma rota válida
        self.logger.log('Nenhuma rota válida encontrada')
        print('Requisição não pode ser atendida pq não tem rotas válidas, boa sorte ai, vlw, flws')
        return None