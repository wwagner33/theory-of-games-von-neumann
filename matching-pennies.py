import mesa
import pygame
import sys

# ==========================================
# 1. LÓGICA DO MESA (MODELO E AGENTES)
# ==========================================

class PlayerAgent(mesa.Agent):
    """Agente que joga Matching Pennies usando estratégias mistas."""
    def __init__(self, unique_id, model, is_player_1):
        # Compatibilidade com Mesa 3.0+
        super().__init__(model)
        self.unique_id = unique_id
        self.is_player_1 = is_player_1
        self.choice = None
        self.score = 0
        self.prob_heads = 0.5 

    def step(self):
        # Fase 1: Decisão Simultânea (Cálculo isolado)
        if self.random.random() < self.prob_heads:
            self.choice = 0 # Cara
        else:
            self.choice = 1 # Coroa

    def advance(self):
        # Fase 2: Resolução do Payoff (Aplicação das regras)
        # Identifica o oponente diretamente através do modelo
        other_agent = self.model.p2 if self.is_player_1 else self.model.p1
        
        # Lógica de Soma Zero
        if self.is_player_1:
            if self.choice == other_agent.choice:
                self.score += 1  # Combinou: J1 ganha
            else:
                self.score -= 1  # Diferente: J1 perde
        else:
            if self.choice == other_agent.choice:
                self.score -= 1  # Combinou: J2 perde
            else:
                self.score += 1  # Diferente: J2 ganha

class MatchingPenniesModel(mesa.Model):
    """Modelo do ambiente de Teoria dos Jogos."""
    def __init__(self):
        super().__init__()
        
        # Inicializa os agentes
        self.p1 = PlayerAgent(1, self, is_player_1=True)
        self.p2 = PlayerAgent(2, self, is_player_1=False)
        
        # Lista simples para iterar sobre os agentes ativos
        self.agentes_ativos = [self.p1, self.p2]
        
        # O DataCollector continua funcionando da mesma forma
        self.datacollector = mesa.DataCollector(
            model_reporters={"P1_Score": lambda m: m.p1.score,
                             "P2_Score": lambda m: m.p2.score}
        )

    def step(self):
        # Substitui o SimultaneousActivation executando as duas fases manualmente
        
        # 1. Todos os agentes decidem sua jogada
        for agente in self.agentes_ativos:
            agente.step()
            
        # 2. Todos os agentes revelam a jogada e calculam o saldo
        for agente in self.agentes_ativos:
            agente.advance()
            
        self.datacollector.collect(self)

# ==========================================
# 2. VISUALIZAÇÃO COM PYGAME
# ==========================================

def draw_text(surface, text, font, color, x, y):
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def draw_graph(surface, data, x, y, w, h, font):
    GRAY, BLUE, RED, BLACK = (200, 200, 200), (50, 100, 200), (200, 50, 50), (0, 0, 0)
    pygame.draw.rect(surface, GRAY, (x, y, w, h), 2)
    draw_text(surface, "Acumulado Jogador 1 (Equilíbrio Teórico = 0)", font, BLACK, x, y - 30)
    
    if len(data) > 1:
        max_val = max(max(data), abs(min(data)), 10)
        points = []
        for i, val in enumerate(data[-w:]):
            px = x + i * (w / min(len(data), w))
            py = y + (h / 2) - (val / max_val) * (h / 2)
            points.append((px, py))
        
        if len(points) >= 2:
            pygame.draw.lines(surface, BLUE, False, points, 2)
            
    pygame.draw.line(surface, RED, (x, y + h//2), (x + w, y + h//2), 1)

def main():
    pygame.init()
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Mesa + Pygame: Matching Pennies")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont('Arial', 24)
    title_font = pygame.font.SysFont('Arial', 32, bold=True)
    WHITE, BLACK, BLUE, RED = (255, 255, 255), (0, 0, 0), (50, 100, 200), (200, 50, 50)

    model = MatchingPenniesModel()
    
    running = True
    simulation_speed = 10 
    round_count = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- AVANÇA O MODELO MESA ---
        model.step()
        round_count += 1
        
        history_p1 = model.datacollector.get_model_vars_dataframe()["P1_Score"].tolist()
        str_choice_1 = "Cara" if model.p1.choice == 0 else "Coroa"
        str_choice_2 = "Cara" if model.p2.choice == 0 else "Coroa"

        # --- RENDERIZAÇÃO ---
        screen.fill(WHITE)
        draw_text(screen, "Simulação Mesa: Matching Pennies", title_font, BLACK, 180, 20)
        
        pygame.draw.rect(screen, BLUE, (50, 100, 300, 150), border_radius=10)
        draw_text(screen, "Agente 1 (Quer Combinar)", font, WHITE, 60, 110)
        draw_text(screen, f"Escolha: {str_choice_1}", font, WHITE, 60, 160)
        draw_text(screen, f"Saldo: {model.p1.score}", font, WHITE, 60, 200)

        pygame.draw.rect(screen, RED, (450, 100, 300, 150), border_radius=10)
        draw_text(screen, "Agente 2 (Quer Diferente)", font, WHITE, 460, 110)
        draw_text(screen, f"Escolha: {str_choice_2}", font, WHITE, 460, 160)
        draw_text(screen, f"Saldo: {model.p2.score}", font, WHITE, 460, 200)
        
        draw_text(screen, f"Rodada: {round_count}", font, BLACK, 350, 280)

        draw_graph(screen, history_p1, 50, 350, 700, 200, font)

        pygame.display.flip()
        clock.tick(simulation_speed)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()