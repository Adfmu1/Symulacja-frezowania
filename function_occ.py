import math

class GCodeParser:
    @staticmethod
    def parse(command, current_position, current_feedrate):
        cmd_parts = command.strip().upper().split()
        if not cmd_parts:
            return {'type': 'UNKNOWN'}
        
        if cmd_parts[0].startswith('F'):
            try:
                new_f = float(cmd_parts[0][1:])
                return {'type': 'UPDATE_FEED', 'f': new_f}
            except:
                return {'type': 'UNKNOWN'}
        
        gcode = cmd_parts[0]
        components = {}
        for part in cmd_parts[1:]:
            key = part[0]
            try:
                components[key] = float(part[1:])
            except ValueError:
                continue

        new_feedrate = components.get('F', current_feedrate)

        if gcode in ['G00', 'G0']:
            return {
                'type': 'G00',
                'x': components.get('X', current_position[0]),
                'y': components.get('Y', current_position[1]),
                'z': components.get('Z', current_position[2]),
                'f': 5000 
            }
        elif gcode in ['G01', 'G1']:
            return {
                'type': 'G01',
                'x': components.get('X', current_position[0]),
                'y': components.get('Y', current_position[1]),
                'z': components.get('Z', current_position[2]),
                'f': new_feedrate
            }
        elif gcode in ['G02', 'G2', 'G03', 'G3']:
            is_cw = gcode in ['G02', 'G2']
            try:
                if 'R' in components:
                    parsed = GCodeParser._parse_r_notation(components, current_position, is_cw)
                else:
                    parsed = GCodeParser._parse_ij_notation(components, current_position, is_cw)
                
                parsed.update({
                    'type': 'ARC',
                    'x': components.get('X', current_position[0]),
                    'y': components.get('Y', current_position[1]),
                    'z': components.get('Z', current_position[2]),
                    'f': new_feedrate
                })
                return parsed
            except Exception as e:
                print(f"Błąd parsowania łuku: {str(e)}")
                return {'type': 'UNKNOWN', 'f': current_feedrate}
        elif gcode in ['M06', 'M6']:
            return {
                'type': 'TOOL_CHANGE',
                'radius': int(cmd_parts[-1])/2 if cmd_parts else 0
            }
        else:
            return {'type': 'UNKNOWN', 'f': current_feedrate}

    @staticmethod
    def _parse_r_notation(components, current_pos, is_cw):
        radius = abs(components['R'])
        x_target = components.get('X', current_pos[0])
        y_target = components.get('Y', current_pos[1])

        dx = x_target - current_pos[0]
        dy = y_target - current_pos[1]
        chord_length = math.hypot(dx, dy)

        if chord_length > 2 * radius:
            raise ValueError(f"Promień {radius} za mały dla cięciwy {chord_length}")

        mid_x = current_pos[0] + dx / 2
        mid_y = current_pos[1] + dy / 2

        perp = [dy, -dx] if is_cw else [-dy, dx]
        perp_length = math.hypot(*perp)
        
        if perp_length > 1e-6:
            perp = [p/perp_length for p in perp]

        offset = math.sqrt(radius**2 - (chord_length/2)**2)
        center_x = mid_x + perp[0] * offset
        center_y = mid_y + perp[1] * offset

        start_angle = math.atan2(current_pos[1] - center_y, current_pos[0] - center_x)
        end_angle = math.atan2(y_target - center_y, x_target - center_x)

        return {
            'center': [center_x, center_y, current_pos[2]],
            'radius': radius,
            'start_angle': start_angle,
            'end_angle': end_angle,
            'is_cw': is_cw,
            'steps': 60
        }

    @staticmethod
    def _parse_ij_notation(components, current_pos, is_cw):
        x_target = components.get('X', current_pos[0])
        y_target = components.get('Y', current_pos[1])
        i_offset = components.get('I', 0.0)
        j_offset = components.get('J', 0.0)

        center_x = current_pos[0] + i_offset
        center_y = current_pos[1] + j_offset
        radius = math.hypot(i_offset, j_offset)

        target_radius = math.hypot(x_target - center_x, y_target - center_y)
        if not math.isclose(radius, target_radius, rel_tol=1e-3):
            raise ValueError(f"Cel ({x_target}, {y_target}) nie leży na łuku (promień {radius:.2f})")

        start_angle = math.atan2(current_pos[1] - center_y, current_pos[0] - center_x)
        end_angle = math.atan2(y_target - center_y, x_target - center_x)

        angular_dist = end_angle - start_angle
        if is_cw and angular_dist > -1e-6:
            angular_dist -= 2 * math.pi
        elif not is_cw and angular_dist < 1e-6:
            angular_dist += 2 * math.pi

        return {
            'center': [center_x, center_y, current_pos[2]],
            'radius': radius,
            'start_angle': start_angle,
            'end_angle': start_angle + angular_dist,
            'is_cw': is_cw,
            'steps': max(50, int(abs(angular_dist) * 50))
        }