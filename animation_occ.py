from animations_occ import GCodeVisualizer

def start_animation(commands, width, length, height):
    vis = GCodeVisualizer(length, height, width)
    for cmd in commands:
        parsed = vis.parser.parse(
            cmd, 
            [vis.last_position.X(), vis.last_position.Y(), vis.last_position.Z()],
            3000
        )
        print(f"Executing: {parsed}")
        
        if parsed['type'] == 'G00':
            vis.g00(parsed['x'], parsed['y'], parsed['z'])
        elif parsed['type'] == 'G01':
            vis.g01(parsed['x'], parsed['y'], parsed['z'])
        elif parsed['type'] == 'ARC':
            vis.g02_g03(parsed)
        elif parsed['type'] == 'TOOL_CHANGE':
            vis.change_tool(parsed['radius'])

    vis.start_display()
