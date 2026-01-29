import random
import pygame
import numpy as np
import pickle
import os


pygame.init()
clock = pygame.time.Clock()

#plant dna layout
#
#64 genes, each gene has four direction genes, then four cell type genes for that direction
#
# example, first ones are whether to grow and what gene that spot will take
# next four are what cell type it will be 32 127 0 86 2 0 2 1
#
#if its under 64 you grow
#if the cell type is 0 its another growing cell
#if its 1 then its a leaf cell
#if its 2 then its a body cell
# if its 3 then it is a seed
#
#0 1 2 3 are whether to grow and chromosome number for next part
#4 5 6 7 are cell type for the spot it left
#
#8 9 10 11 are special grow conditions for each direction
#12 13 14 15 are numbers to tune grow conditions for each direction
#
#


class World:
	current_location = 0
	plantid = 1
	SCREEN_WIDTH = 1200
	SCREEN_HEIGHT = 800
	GRID_WIDTH = 600
	GRID_HEIGHT = 70
	GRID_DISPLAYED_WIDTH = SCREEN_WIDTH//10
	template = [0] * GRID_HEIGHT
	plant_grid = np.array([template.copy()]*GRID_WIDTH)
	gene_grid = plant_grid.copy()
	cell_type_grid = plant_grid.copy()
	plant_genes = {}
	boxes_to_update = []
	plant_energy = {}
	plant_life = {}
	growCellLocation = []
	starting_energy = 50
	mutation_rate = 8
	leaf_cells = []
	sunlight_level = 5.0
	slow = True
	numPlantsPerSeed = 1
	plant_trunk_locations = []

class colors:
	sky_color = (50, 150, 255)
	leaf_colors = [(50, 100, 50), (0, 80, 0), (50, 150, 100)]
	stem_colors = [(80, 20, 20), (100, 20, 20), (200, 200, 0)]
	seed_colors = [(255, 0, 100), (255, 0, 40), (180, 0, 0)]
	grow_cell_colors = [(255, 255, 255)]
	

def generate_random_plant():
	plant = []
	for gene_number in range(64):
		gene = []
		for point_number in range(4):
			point = random.randrange(1, 128)
			while point == gene_number:
				point = random.randrange(1, 128)
			gene.append(point)
		for point_number in range(4):
			point = random.randrange(0,4)
			while point == gene_number:
				point = random.randrange(0, 4)
			gene.append(point)
		for point_number in range(4):
			point = random.randrange(0,4)
			while point == gene_number:
				point = random.randrange(0, 4)
			gene.append(point)
		for point_number in range(4):
			point = random.randrange(0,128)
			while point == gene_number:
				point = random.randrange(0, 128)
			gene.append(point)
		plant.append(gene)

	World.plant_genes[World.plantid] = plant.copy()
	new_plant_x = random.randrange(0, World.GRID_WIDTH)
	World.plant_grid[new_plant_x, World.GRID_HEIGHT-1] = World.plantid
	World.boxes_to_update.append([new_plant_x, World.GRID_HEIGHT-1])
	World.plant_energy[World.plantid] = World.starting_energy
	World.plant_life[World.plantid] = 0
	World.plantid += 1
	World.growCellLocation.append([new_plant_x, World.GRID_HEIGHT-1])
	World.plant_trunk_locations.append((World.plantid - 1, new_plant_x, World.GRID_HEIGHT - 1))



def grow_plants():
    newGrowCellLocation = []

    for box in World.growCellLocation:
        x, y = box
        plant_id = World.plant_grid[x, y]
        if plant_id == 0:
            continue

        # Only grow cells can grow
        if World.cell_type_grid[x, y] != 0:
            continue

        # Energy check
        if World.plant_energy[plant_id] < 5:
            newGrowCellLocation.append(box)
            continue

        genes = World.plant_genes[plant_id]
        gene_index = World.gene_grid[x, y]

        keep_old_tip = True

        for direction in range(4):
            if genes[gene_index][direction] >= 64:
                continue
            if genes[gene_index][direction+ 8] == 2:
                if random.randrange(0, genes[gene_index][direction + 12] + 2) == 0:
                    continue
            if genes[gene_index][direction+ 8] == 1:
                if y > genes[gene_index][direction + 12]:
                    continue

            nx, ny = x, y
            if direction == 0:
                nx -= 1
            elif direction == 1:
                nx += 1
            elif direction == 2:
                ny -= 1
            elif direction == 3:
                ny += 1


			
            nx = nx % World.GRID_WIDTH

            # Bounds check
            if nx < 0 or nx >= World.GRID_WIDTH or ny < 0 or ny >= World.GRID_HEIGHT:
                continue

            # Collision check
            if World.plant_grid[nx, ny] != 0:
                continue

            # Place new cell
            World.plant_grid[nx, ny] = plant_id
            World.gene_grid[nx, ny] = genes[gene_index][direction]

            cell_type = genes[gene_index][direction + 4]

            # ---- Cell type handling ----
            if cell_type == 2:  # stem
                World.plant_energy[plant_id] -= .5
                World.cell_type_grid[x, y] = 2
                keep_old_tip = False

            elif cell_type == 1:  # leaf
                World.plant_energy[plant_id] -= 1
                World.cell_type_grid[x, y] = 1
                World.leaf_cells.append([x, y])
                keep_old_tip = False

            elif cell_type == 3:  # seed (terminal)
                World.plant_energy[plant_id] -= 20
                World.cell_type_grid[x, y] = 3
                keep_old_tip = False

            else:  # grow -> grow
                World.plant_energy[plant_id] -= 5
                World.cell_type_grid[x, y] = 0
                World.gene_grid[x, y] = genes[gene_index][direction]

            # New location is always a grow tip
            World.cell_type_grid[nx, ny] = 0
            newGrowCellLocation.append([nx, ny])

            break  # only one growth per tick

        # Preserve old grow tip if it wasn't consumed
        if keep_old_tip:
            newGrowCellLocation.append(box)

    World.growCellLocation = newGrowCellLocation

				

					

def mutate_genes(genes):
	for times in range(World.mutation_rate):
		genes[random.randrange(0, 64)][random.randrange(0, 4)] = random.randrange(0, 128)
		genes[random.randrange(0, 64)][random.randrange(4, 8)] = random.randrange(0, 3)
		genes[random.randrange(0, 64)][random.randrange(8, 12)] = random.randrange(0, 4)
		genes[random.randrange(0, 64)][random.randrange(12, 16)] = random.randrange(0, 128)
	return genes


def give_energy():
    energy_gained = {plant_id: 0 for plant_id in World.plant_energy}  # track energy from light

    for x in range(World.GRID_WIDTH):
        light = World.sunlight_level  # start with full light at top

        for y in range(World.GRID_HEIGHT):
            cell_type = World.cell_type_grid[x, y]
            plant_id = World.plant_grid[x, y]

            if plant_id != 0:
                if cell_type == 1:  # leaf
                    gained = light
                    World.plant_energy[plant_id] += gained
                    energy_gained[plant_id] += gained
                    light *= 0.4  # blocks light below
                elif cell_type == 2:  # stem
                    light *= 0.6
                elif cell_type == 0:  # grow cell
                    light *= 0.6
                elif cell_type == 3:  # seed
                    light *= 0.8
                if World.plant_grid[x, max(y-1, 0)] == 0:
                   light *= 2
            if light < 0.01:
                break

    return energy_gained


def oldmaintenance_cost():
	for plant_id in World.plant_energy:
		cell_count = np.count_nonzero(World.plant_grid == plant_id)
		World.plant_energy[plant_id] -= cell_count * 0.3 

def get_stump_location(plant_id):
    cells = np.argwhere(World.plant_grid == plant_id)
    if len(cells) == 0:
        return None

    # lowest y = stump
    max_y = np.max(cells[:, 1])
    stump_cells = cells[cells[:, 1] == max_y]

    # average x in case of multiple base cells
    stump_x = int(np.mean(stump_cells[:, 0]))

    return stump_x, max_y

def maintenance_cost():
    BASE_COST = 0.03       # baseline metabolic cost
    EXP_FACTOR = 1.05      # exponential distance penalty
    SIDE_PENALTY = 1.2     # horizontal cost multiplier

    for plant_id in list(World.plant_energy.keys()):
        stump = get_stump_location(plant_id)
        if stump is None:
            continue

        stump_x, stump_y = stump
        total_cost = 0.0

        cells = np.argwhere(World.plant_grid == plant_id)

        for x, y in cells:
            vertical_dist = stump_y - y
            horizontal_dist = abs(x - stump_x)

            # effective transport distance
            dist = vertical_dist + SIDE_PENALTY * horizontal_dist

            # exponential transport cost
            cost = BASE_COST * (EXP_FACTOR ** dist)
            total_cost += cost

        World.plant_energy[plant_id] -= total_cost




def remove_plants():
    newGrowCellLocation = []
    World.leaf_cells = []

    reproduced_this_tick = set()  # track which plants already reproduced

    # Gather all living plants
    living_plants = list(World.plant_life.keys())

    for plant_id in living_plants:
        # Age the plant
        World.plant_life[plant_id] += 1

        # Determine plant height and size
        plant_cells = np.argwhere(World.plant_grid == plant_id)
        if len(plant_cells) == 0:
            continue
        plant_height = World.GRID_HEIGHT - np.min(plant_cells[:, 1])
        plant_size = len(plant_cells)

        # Decide if plant should die:
        # 1. Too old
        # 2. No energy
        # 3. Shaded (energy < minimal)
        die = (
            World.plant_energy[plant_id] <= 0
            or World.plant_life[plant_id] > max(World.plant_genes[plant_id][0][5], 30)
            or (plant_size < 3 and World.plant_energy[plant_id] < 2)
        )

        if not die:
            continue  # plant survives

        # Remove plant cells
        for loc in plant_cells:
            x, y = loc
            cell_type = World.cell_type_grid[x, y]

            # Keep track of leaves for light calculations
            if cell_type == 1:
                World.leaf_cells.append([x, y])

            # Only reproduce if seed cell and plant big enough and hasn't reproduced yet
            if (
                cell_type == 3
                and plant_id not in reproduced_this_tick
                and plant_size >= 5
                and World.plant_energy[plant_id] > 10
            ):
                if random.randrange(0, 10) == 0:
                    reproduced_this_tick.add(plant_id)
                genes = [g.copy() for g in World.plant_genes[plant_id]]
                genes = mutate_genes(genes)

                # Attempt to place one new seed
                max_distance = World.GRID_HEIGHT-y
                new_x = x + 2 * random.randint(-max_distance, max_distance)
                new_x = max(0, min(World.GRID_WIDTH - 1, new_x))

                if World.plant_grid[new_x, World.GRID_HEIGHT - 1] == 0:
                    World.plant_grid[new_x, World.GRID_HEIGHT - 1] = World.plantid
                    World.growCellLocation.append([new_x, World.GRID_HEIGHT - 1])
                    World.plant_trunk_locations.append([new_x, World.GRID_HEIGHT - 1])
                    World.plant_genes[World.plantid] = [g.copy() for g in genes]
                    World.plant_energy[World.plantid] = World.starting_energy
                    World.plant_life[World.plantid] = 0
                    World.plantid += 1

            # Clear the old cell
            World.plant_grid[x, y] = 0
            World.cell_type_grid[x, y] = 0
            World.gene_grid[x, y] = 0

        # Remove plant metadata
        del World.plant_energy[plant_id]
        del World.plant_life[plant_id]
        del World.plant_genes[plant_id]

    # Rebuild leaf cells for energy calculation
    for x in range(World.GRID_WIDTH):
        for y in range(World.GRID_HEIGHT):
            if World.cell_type_grid[x, y] == 1:
                World.leaf_cells.append([x, y])

    # No need to extend growCellLocation with newGrowCellLocation, seeds are already added


def make_surface(color):
    s = pygame.Surface((10, 10))
    s.fill(color)
    return s

BOXES = {
    "sky": make_surface(colors.sky_color),
    "leaf": make_surface(colors.leaf_colors[1]),
    "stem": make_surface(colors.stem_colors[1]),
    "seed": make_surface(colors.seed_colors[1]),
	"growCell": make_surface(colors.grow_cell_colors[0])
}


def render_world(update_everything = True):
	if update_everything:
		for x_loc in range(World.GRID_DISPLAYED_WIDTH):
			for y_loc in range(World.GRID_HEIGHT):
				box = pygame.Surface((10, 10))
				plant_id = World.plant_grid[x_loc+World.current_location, y_loc]
				if plant_id == 0:
					screen.blit(BOXES["sky"], (x_loc*10, y_loc*10))
				else:
					if World.cell_type_grid[x_loc+World.current_location, y_loc] == 0:
						screen.blit(BOXES["growCell"], (x_loc*10, y_loc*10))
					elif World.cell_type_grid[x_loc+World.current_location, y_loc] == 1:
						screen.blit(BOXES["leaf"], (x_loc*10, y_loc*10))
					elif World.cell_type_grid[x_loc+World.current_location, y_loc] == 2:
						screen.blit(BOXES["stem"], (x_loc*10, y_loc*10))
					elif World.cell_type_grid[x_loc+World.current_location, y_loc] == 3:
						screen.blit(BOXES["seed"], (x_loc*10, y_loc*10))
		#random.seed()
	else:
		for loc in World.boxes_to_update:
			x_loc = loc[0]
			y_loc = loc[1]
			box = pygame.Surface((10, 10))
			plant_id = World.plant_grid[x_loc+World.current_location, y_loc]
			if plant_id == 0:
				color = colors.sky_color
				box.fill(color)
			else:
				random.seed(int(plant_id))
				color = colors.stem_colors[random.randrange(0, len(colors.stem_colors))]
				box.fill(color)
			screen.blit(box, (x_loc*10, y_loc*10))
		random.seed()

screen = pygame.display.set_mode((World.SCREEN_WIDTH, World.SCREEN_HEIGHT))

def rebuild_leaf_cells():
    World.leaf_cells = []
    for x in range(World.GRID_WIDTH):
        for y in range(World.GRID_HEIGHT):
            if World.cell_type_grid[x, y] == 1:
                World.leaf_cells.append([x, y])





def save_world(filename="world_save.pkl"):
    world_state = {
        "plant_grid": World.plant_grid,
        "gene_grid": World.gene_grid,
        "cell_type_grid": World.cell_type_grid,

        "plant_genes": World.plant_genes,
        "plant_energy": World.plant_energy,
        "plant_life": World.plant_life,

        "growCellLocation": World.growCellLocation,
        "leaf_cells": World.leaf_cells,
        "plant_trunk_locations": World.plant_trunk_locations,

        "plantid": World.plantid,
        "current_location": World.current_location,

        "sunlight_level": World.sunlight_level,
        "mutation_rate": World.mutation_rate,
        "starting_energy": World.starting_energy,
        "tick": tick,
    }

    with open(filename, "wb") as f:
        pickle.dump(world_state, f, protocol=pickle.HIGHEST_PROTOCOL)

    print(f"World saved to {os.path.abspath(filename)}")


def load_world(filename="world_save.pkl"):
    global tick

    if not os.path.exists(filename):
        print("No save file found.")
        return

    with open(filename, "rb") as f:
        world_state = pickle.load(f)

    World.plant_grid = world_state["plant_grid"]
    World.gene_grid = world_state["gene_grid"]
    World.cell_type_grid = world_state["cell_type_grid"]

    World.plant_genes = world_state["plant_genes"]
    World.plant_energy = world_state["plant_energy"]
    World.plant_life = world_state["plant_life"]

    World.growCellLocation = world_state["growCellLocation"]
    World.leaf_cells = world_state["leaf_cells"]
    World.plant_trunk_locations = world_state["plant_trunk_locations"]

    World.plantid = world_state["plantid"]
    World.current_location = world_state["current_location"]

    World.sunlight_level = world_state["sunlight_level"]
    World.mutation_rate = world_state["mutation_rate"]
    World.starting_energy = world_state["starting_energy"]

    tick = world_state["tick"]

    print(f"World loaded from {filename}")

    render_world(True)



generate_random_plant()

tick = 0
done = False
while not done:
	tick += 1
	grow_plants()
	rebuild_leaf_cells()
	give_energy()
	maintenance_cost()
	if tick % 10 == 0:
		remove_plants()
	render_world()

	if tick % 1000 == 0:
		save_world("autosave.pkl")

	for event in pygame.event.get(): # key presses
		if event.type == pygame.QUIT:
			done = True
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_SPACE:
				for i in range(50):
					generate_random_plant()
			if event.key == pygame.K_RIGHT:
				World.current_location += 10
				if World.current_location > World.GRID_WIDTH - World.GRID_DISPLAYED_WIDTH:
					World.current_location = 0
				render_world(True)
			if event.key == pygame.K_LEFT:
				World.current_location -= 10
				if World.current_location < 0:
					World.current_location = World.GRID_WIDTH - World.GRID_DISPLAYED_WIDTH
				render_world(True)
			if event.key == pygame.K_f:
				World.slow = not World.slow
			if event.key == pygame.K_c:
				for i in range(3):
					for xloc in range(World.GRID_WIDTH):
						World.plant_grid[xloc, World.GRID_HEIGHT-1-i] = 0
						World.cell_type_grid[xloc, World.GRID_HEIGHT - 1 - i] = 0
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_s:
					save_world()
			if event.key == pygame.K_l:
				load_world()
	if World.slow:
		clock.tick(10) #maximum frame rate
	pygame.display.flip()

