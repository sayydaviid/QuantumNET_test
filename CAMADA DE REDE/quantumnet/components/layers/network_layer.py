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

        Returns:
            bool: True se todos os canais tiverem pelo menos um par EPR, False caso contrário.
        """

        for edge in self._network.graph.edges:
            if len(self._network.get_eprs_from_edge(edge[0], edge[1])) == 0:
                self.logger.log(f'No EPR pairs between {edge[0]} and {edge[1]}')
                return False
        self.logger.log(f'Há pelo menos 1 par EPR nesses canais')
        return True
    

    def verify_nodes(self):
        """
        Verifica se todos os nós possuem pelo menos 2 qubits.
        
        Returns:
            bool : True se todos os nós possuem pelo menos 2 qubits, False caso contrário.
        """
        for node in self._network.graph.nodes:
            host = self._network.get_host(node)
            if len(host.memory) < 2:
                self.logger.log(f'Nós {node} não apresentam nem 2 qubits pelo menos')
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
        self.logger.log('Nenhuma rota válida encontrada.')
        print('Requisição não pode ser atendida pq não tem rotas válidas.')
        return None
    

    def entanglement_swapping(self, node1, node2, node3, node4):
        """
        Realiza o Entanglement Swapping entre duas pares de canais adjacentes.
        
        args:
            node1 (int): ID do nó inicial.
            node2 (int): ID do nó intermediário.
            node3 (int): ID do nó intermediário.
            node4 (int): ID do nó final.
                
        returns:
            bool: True se o Entanglement Swapping for bem-sucedido, False caso contrário.
        """
        # Primeira operação de Entanglement Swapping (node1, node2) e (node2, node3)
        if not self._network.graph.has_edge(node1, node2) or not self._network.graph.has_edge(node2, node3):
            self.logger.log(f'Canais entre {node1}-{node2} ou {node2}-{node3} não existem')
            return False
        
        #Obtenção do par ERS no canal entre os nós escolhidos
        try:
            epr1 = self._network.get_eprs_from_edge(node1, node2)[0]
            epr2 = self._network.get_eprs_from_edge(node2, node3)[0]
        except IndexError:
            self.logger.log(f'Não há pares EPRs suficientes para realizar o entanglement swapping entre {node1}-{node2} e {node2}-{node3}')
            return False

        #Adquirir a fidelidade dos pares EPRs obtidos 
        fidelity1 = epr1.get_current_fidelity()
        fidelity2 = epr2.get_current_fidelity()

        #Probabilidade de sucesso do entanglement swapping 
        success_prob = fidelity1 * fidelity2 + (1 - fidelity1) * (1 - fidelity2)
        if uniform(0, 1) > success_prob:
            self.logger.log(f'Entanglement Swapping falhou entre {node1}-{node2} e {node2}-{node3}')
            return False

        #Registra e calcula uma nova fidelidade e cria um novo par EPR virtual com essa fidelidade.
        new_fidelity1 = (fidelity1 * fidelity2) / ((fidelity1 * fidelity2) + (1 - fidelity1) * (1 - fidelity2))
        epr_virtual1 = Epr((node1, node3), new_fidelity1)

        if not self._network.graph.has_edge(node1, node3):
            self._network.graph.add_edge(node1, node3, eprs=[])

        #Adiciona o par EPR virtual ao canal entre os nós e remore os pares EPRs originais do canal
        self._network.physical.add_epr_to_channel(epr_virtual1, (node1, node3))
        self._network.physical.remove_epr_from_channel(epr1, (node1, node2))
        self._network.physical.remove_epr_from_channel(epr2, (node2, node3))

        # Segunda operação de Entanglement Swapping (node1, node3) e (node3, node4)
        if not self._network.graph.has_edge(node3, node4):
            self.logger.log(f'Canal entre {node3} e {node4} não existe')
            return False

        #Tenta obter o primeiro par EPR entre os nós
        try:
            epr3 = self._network.get_eprs_from_edge(node3, node4)[0]
        except IndexError:
            self.logger.log(f'Não há pares EPRs válidos para o entaglement swapping entre {node3} e {node4}')
            return False

        #Adquiri a fidelidade e depois verifica a probabilidade de sucesso do entanglement Swapping
        fidelity3 = epr3.get_current_fidelity()
        success_prob = new_fidelity1 * fidelity3 + (1 - new_fidelity1) * (1 - fidelity3)
        if uniform(0, 1) > success_prob:
            self.logger.log(f'Entanglement Swapping falhou entre {node1}-{node3} e {node3}-{node4}')
            return False

        #Registra e calcula uma nova fidelidade e cria um novo par EPR virtual com essa fidelidade.
        new_fidelity2 = (new_fidelity1 * fidelity3) / ((new_fidelity1 * fidelity3) + (1 - new_fidelity1) * (1 - fidelity3))
        epr_virtual2 = Epr((node1, node4), new_fidelity2)

        if not self._network.graph.has_edge(node1, node4):
            self._network.graph.add_edge(node1, node4, eprs=[])

        #Adiciona o par EPR virtual ao canal entre os nós e remore os pares EPRs originais do canal
        self._network.physical.add_epr_to_channel(epr_virtual2, (node1, node4))
        self._network.physical.remove_epr_from_channel(epr_virtual1, (node1, node3))
        self._network.physical.remove_epr_from_channel(epr3, (node3, node4))

        self.logger.log(f'Sucesso do Entanglement Swapping no {node1} para {node4} através do {node2} e {node3}')
        return True

