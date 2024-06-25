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
    
    
    
# 2. Estabelecer a rota escolhida
# a. Caso 1: Rota válida (por enquanto só estamos considerando esse ponto de partida)
# → Nesse caso todas as rotas tem pelo menos 1 par EPR e 2 qubits disponíveis para
# estabelecer a rota.
# #Ação:
# Realizar o protocolo de Entanglement Swapping → de forma “recursiva” ao longo da
# rota escolhida
# Entanglement Swapp (rota_escolhida)
# ES (primeira_parte_da_rota)....etc
# ES vai juntar dois pares EPR, um de cada canal (não do mesmo canal como na
# purificação), e formar um novo par EPR virtual → pode criar um entidade ou algo assim
# Exemplo: Rota = 3,5,7,9
# ES (3,5 ; 5,7) → Vai juntar 1 par EPR que está no canal (3,5) com 1 par EPR que está no
# canal (5,7) = 1 par EPR_virtual que “está” no canal (3,7)
# ES (3,7 ; 7,9) → vai juntar 1 EPR_virtual que está no canal (3,7) com 1 par epr que está no
# canal 7,9 = 1 par EPR_virtual que está no canal (7,9)
# *No final de cada operação, os EPR originais são destruídos (inclusive os virtuais)
# Probabilidade de Sucesso do Entanglement Swapping
# >Cada Canal tem a sua → Adicionar isso como propriedade do canal
# Fidelidade Final ao final do Entanglement Swapping
# Ffinal = F1*F2 + ( (1-F1) *(1-F2) ) → Só vamos assumir canais Pauli homogêneos
# b. Caso 2: Caso o Sucesso do Entanglement Swapping falhe em algum ponto
# 1. Verificar se existe par EPR adicionar nos canais onde ocorreu a falha
# a. se sim, tenta novamente e volta para o caso 1
# 2. Caso um ou +1 de um dos canais tenham falha:
# a. Gera Requisição de Criação de par EPR para a camada
# b. Caso haja falha na camada de enlace, pede novamente x= +1 e depois
# desiste
# c. com o par EPR criado, volta para o caso 1



    def perform_entanglement_swapping(self, path):
        """
        Realiza o protocolo de Entanglement Swapping ao longo da rota escolhida.
        
        args:
            path (list): Lista de nós que representam a rota escolhida.
            
        returns:
            bool: True se o Entanglement Swapping for bem-sucedido, False caso contrário.
        """
        while len(path) > 2:
            node = path[0]
            next_node = path[1]
            next_next_node = path[2]

            success = self.entanglement_swapping(node, next_node, next_next_node)
            if not success:
                # Verifica se existe um par EPR adicional no canal onde ocorreu a falha
                if len(self._network.get_eprs_from_edge(node, next_node)) < 1 or len(self._network.get_eprs_from_edge(next_node, next_next_node)) < 1:
                    # Gera requisição de criação de par EPR
                    self._link_layer.request(node, next_node)
                    self._link_layer.request(next_node, next_next_node)
                    # Tenta novamente o Entanglement Swapping
                    continue
                else:
                    # Falha no Entanglement Swapping e não há par EPR adicional disponível
                    self.logger.log('Entanglement Swapping failed and no additional EPR pairs available')
                    return False
            # Atualiza a rota removendo o nó intermediário
            path.pop(1)
        
        self.logger.log('Entanglement Swapping successful along the path')
        return True

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
            self.logger.log(f'Edges between {node1}-{node2} or {node2}-{node3} do not exist')
            return False

        try:
            epr1 = self._network.get_eprs_from_edge(node1, node2)[0]
            epr2 = self._network.get_eprs_from_edge(node2, node3)[0]
        except IndexError:
            self.logger.log(f'Not enough EPR pairs available for swapping between {node1}-{node2} and {node2}-{node3}')
            return False

        fidelity1 = epr1.get_current_fidelity()
        fidelity2 = epr2.get_current_fidelity()

        success_prob = fidelity1 * fidelity2 + (1 - fidelity1) * (1 - fidelity2)
        if uniform(0, 1) > success_prob:
            self.logger.log(f'Entanglement Swapping failed between {node1}-{node2} and {node2}-{node3}')
            return False

        new_fidelity1 = (fidelity1 * fidelity2) / ((fidelity1 * fidelity2) + (1 - fidelity1) * (1 - fidelity2))
        epr_virtual1 = Epr((node1, node3), new_fidelity1)

        if not self._network.graph.has_edge(node1, node3):
            self._network.graph.add_edge(node1, node3, eprs=[])

        self._network.physical.add_epr_to_channel(epr_virtual1, (node1, node3))
        self._network.physical.remove_epr_from_channel(epr1, (node1, node2))
        self._network.physical.remove_epr_from_channel(epr2, (node2, node3))

        # Segunda operação de Entanglement Swapping (node1, node3) e (node3, node4)
        if not self._network.graph.has_edge(node3, node4):
            self.logger.log(f'Edge between {node3} and {node4} does not exist')
            return False

        try:
            epr3 = self._network.get_eprs_from_edge(node3, node4)[0]
        except IndexError:
            self.logger.log(f'Not enough EPR pairs available for swapping between {node3} and {node4}')
            return False

        fidelity3 = epr3.get_current_fidelity()
        success_prob = new_fidelity1 * fidelity3 + (1 - new_fidelity1) * (1 - fidelity3)
        if uniform(0, 1) > success_prob:
            self.logger.log(f'Entanglement Swapping failed between {node1}-{node3} and {node3}-{node4}')
            return False

        new_fidelity2 = (new_fidelity1 * fidelity3) / ((new_fidelity1 * fidelity3) + (1 - new_fidelity1) * (1 - fidelity3))
        epr_virtual2 = Epr((node1, node4), new_fidelity2)

        if not self._network.graph.has_edge(node1, node4):
            self._network.graph.add_edge(node1, node4, eprs=[])

        self._network.physical.add_epr_to_channel(epr_virtual2, (node1, node4))
        self._network.physical.remove_epr_from_channel(epr_virtual1, (node1, node3))
        self._network.physical.remove_epr_from_channel(epr3, (node3, node4))

        self.logger.log(f'Entanglement Swapping successful from {node1} to {node4} through {node2} and {node3}')
        return True

