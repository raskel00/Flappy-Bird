"""
Le jeu Flappy Bird. Fait avec Python et Pygame.
"""
import pygame
import random
import os
import time
import neat
import visualize
import pickle
pygame.font.init()  # Initialisation des polices

WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

pipe_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")).convert_alpha())
bg_img = pygame.transform.scale(pygame.image.load(os.path.join("imgs", "bg.png")).convert_alpha(), (600, 900))
bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird" + str(x) + ".png"))) for x in range(1, 4)]
base_img = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")).convert_alpha())

gen = 0

class Bird:
    """
    Classe Bird représentant le flappy bird
    """
    MAX_ROTATION = 25
    IMGS = bird_images
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        """
        Initialise l'objet
        :param x: position de départ en x (int)
        :param y: position de départ en y (int)
        :return: None
        """
        self.x = x
        self.y = y
        self.tilt = 0  # degrés d'inclinaison
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        """
        Fait sauter l'oiseau
        :return: None
        """
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        """
        Fait bouger l'oiseau
        :return: None
        """
        self.tick_count += 1

        # Pour l'accélération vers le bas
        displacement = self.vel * (self.tick_count) + 0.5 * (3) * (self.tick_count) ** 2  # calcule le déplacement

        # Vitesse terminale
        if displacement >= 16:
            displacement = (displacement / abs(displacement)) * 16

        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:  # inclinaison vers le haut
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:  # inclinaison vers le bas
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        """
        Dessine l'oiseau
        :param win: fenêtre ou surface pygame
        :return: None
        """
        self.img_count += 1

        # Pour l'animation de l'oiseau, boucle à travers trois images
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # Donc quand l'oiseau plonge, il ne bat pas des ailes
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        # Incline l'oiseau
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        """
        Obtient le masque pour l'image actuelle de l'oiseau
        :return: None
        """
        return pygame.mask.from_surface(self.img)


class Pipe():
    """
    Représente un tuyau
    """
    GAP = 200
    VEL = 5

    def __init__(self, x):
        """
        Initialise l'objet tuyau
        :param x: int
        :param y: int
        :return" None
        """
        self.x = x
        self.height = 0

        # Où se trouvent le haut et le bas du tuyau
        self.top = 0
        self.bottom = 0

        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

        self.passed = False

        self.set_height()

    def set_height(self):
        """
        Définir la hauteur du tuyau, depuis le haut de l'écran
        :return: None
        """
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        """
        Déplace le tuyau en fonction de la vélocité
        :return: None
        """
        self.x -= self.VEL

    def draw(self, win):
        """
        Dessine le haut et le bas du tuyau
        :param win: fenêtre/surface pygame
        :return: None
        """
        # Dessine le haut
        win.blit(self.PIPE_TOP, (self.x, self.top))
        # Dessine le bas
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))


    def collide(self, bird, win):
        """
        Renvoie si un point est en collision avec le tuyau
        :param bird: objet Bird
        :return: Bool
        """
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True

        return False

class Base:
    """
    Représente le sol en mouvement du jeu
    """
    VEL = 5
    WIDTH = base_img.get_width()
    IMG = base_img

    def __init__(self, y):
        """
        Initialise l'objet
        :param y: int
        :return: None
        """
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        """
        Déplace le sol pour qu'il semble défiler
        :return: None
        """
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        """
        Dessine le sol. Ce sont deux images qui bougent ensemble.
        :param win: la surface/fenêtre pygame
        :return: None
        """
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def blitRotateCenter(surf, image, topleft, angle):
    """
    Tourne une surface et la blit sur la fenêtre
    :param surf: la surface sur laquelle blitter
    :param image: la surface de l'image à tourner
    :param topLeft: la position en haut à gauche de l'image
    :param angle: une valeur flottante pour l'angle
    :return: None
    """
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)

    surf.blit(rotated_image, new_rect.topleft)

def draw_window(win, birds, pipes, base, score, gen, pipe_ind):
    """
    Dessine la fenêtre pour la boucle de jeu principale
    :param win: surface de fenêtre pygame
    :param bird: un objet Bird
    :param pipes: liste de tuyaux
    :param score: score du jeu (int)
    :param gen: génération actuelle
    :param pipe_ind: index du tuyau le plus proche
    :return: None
    """
    if gen == 0:
        gen = 1
    win.blit(bg_img, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        # Dessine les lignes de l'oiseau au tuyau
        if DRAW_LINES:
            try:
                pygame.draw.line(win, (255, 0, 0), (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2, pipes[pipe_ind].height), 5)
                pygame.draw.line(win, (255, 0, 0), (bird.x + bird.img.get_width() / 2, bird.y + bird.img.get_height() / 2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2, pipes[pipe_ind].bottom), 5)
            except:
                pass
        # Dessine l'oiseau
        bird.draw(win)

    # Score
    score_label = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # Générations
    score_label = STAT_FONT.render("Generations: " + str(gen - 1), 1, (255, 255, 255))
    win.blit(score_label, (10, 10))

    # Vivants
    score_label = STAT_FONT.render("Vivants: " + str(len(birds)), 1, (255, 255, 255))
    win.blit(score_label, (10, 50))

    pygame.display.update()


def eval_genomes(genomes, config):
    """
    Exécute la simulation de la population actuelle
    d'oiseaux et définit leur aptitude en fonction de la distance parcourue dans le jeu.
    """
    global WIN, gen
    win = WIN
    gen += 1

    # Commence par créer des listes contenant le génome lui-même,
    # le réseau neuronal associé au génome et l'objet oiseau qui utilise ce réseau pour jouer
    nets = []
    birds = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0  # commence avec un niveau d'aptitude de 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        ge.append(genome)

    base = Base(FLOOR)
    pipes = [Pipe(700)]
    score = 0

    clock = pygame.time.Clock()

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():  # détermine si l'on doit utiliser le premier ou le deuxième tuyau à l'écran pour l'entrée du réseau neuronal
                pipe_ind = 1

        for x, bird in enumerate(birds):  # donne à chaque oiseau une aptitude de 0,1 pour chaque cadre où il reste en vie
            ge[x].fitness += 0.1
            bird.move()

            # Envoie la position de l'oiseau, la position du tuyau supérieur et la position du tuyau inférieur et détermine à partir du réseau s'il faut sauter ou non
            output = nets[birds.index(bird)].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:  # Nous utilisons une fonction d'activation tanh donc le résultat sera entre -1 et 1. Si supérieur à 0,5, saut
                bird.jump()

        base.move()

        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            # Vérifie la collision
            for bird in birds:
                if pipe.collide(bird, win):
                    ge[birds.index(bird)].fitness -= 1
                    nets.pop(birds.index(bird))
                    ge.pop(birds.index(bird))
                    birds.pop(birds.index(bird))

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True

        if add_pipe:
            score += 1
            # Peut ajouter cette ligne pour donner plus de récompense pour passer à travers un tuyau (pas obligatoire)
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            pipes.remove(r)

        for bird in birds:
            if bird.y + bird.img.get_height() - 10 >= FLOOR or bird.y < -50:
                nets.pop(birds.index(bird))
                ge.pop(birds.index(bird))
                birds.pop(birds.index(bird))

        draw_window(WIN, birds, pipes, base, score, gen, pipe_ind)

        # Arrête si le score devient suffisamment grand
        '''if score > 20:
            pickle.dump(nets[0],open("best.pickle", "wb"))
            break'''


def run(config_file):
    """
    Exécute l'algorithme NEAT pour entraîner un réseau neuronal à jouer à Flappy Bird.
    :param config_file: emplacement du fichier de configuration
    :return: None
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)

    # Crée la population, qui est l'objet de plus haut niveau pour une exécution NEAT.
    p = neat.Population(config)

    # Ajoute un reporter stdout pour afficher les progrès dans le terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    #p.add_reporter(neat.Checkpointer(5))

    # Exécute jusqu'à 50 générations.
    winner = p.run(eval_genomes, 50)

    # Affiche les statistiques finales
    print('\nMeilleur génome:\n{!s}'.format(winner))


if __name__ == '__main__':
    # Détermine le chemin vers le fichier de configuration. Cette manipulation du chemin est
    # ici pour que le script s'exécute correctement quel que soit le
    # répertoire de travail actuel.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    run(config_path)
