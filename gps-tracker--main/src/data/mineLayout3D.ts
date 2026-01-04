import { MineLayout, MineNode, MineTunnel, MineLevel } from "@/types/mine3d";

const CENTER_LAT = 22.292675;
const CENTER_LNG = 73.366018;

const n = (id: string, x: number, y: number, z: number, type: MineNode['type'] = 'junction', label?: string): MineNode => ({
  id,
  position: { x, y, z },
  type,
  label
});

const t = (id: string, start: string, end: string, type: MineTunnel['type'] = 'level_tunnel', width: number = 4): MineTunnel => ({
  id,
  startNodeId: start,
  endNodeId: end,
  type,
  width
});

const nodes: MineNode[] = [
  n('surf_entry', 0, 0, 0, 'shaft_entry', 'Main Shaft Entry'),
  n('shaft_l1', 0, -50, 0, 'junction', 'Level 1 Station'),
  n('shaft_l2', 0, -150, 0, 'junction', 'Level 2 Station'),
  n('shaft_l3', 0, -250, 0, 'junction', 'Level 3 Station'),
  n('shaft_bottom', 0, -300, 0, 'end', 'Sump'),
  n('l1_n1', 50, -50, 20, 'junction'),
  n('l1_n2', 100, -50, 40, 'end', 'Workshop'),
  n('l1_n3', -60, -50, 10, 'junction'),
  n('l1_n4', -120, -50, -30, 'end', 'Storage'),
  n('l1_loop_1', 40, -50, -40, 'junction'),
  n('l1_loop_2', -20, -50, -50, 'junction'),
  n('l2_n1', 20, -150, 80, 'junction'),
  n('l2_n2', 40, -150, 150, 'end', 'Face A'),
  n('l2_n3', -30, -150, 60, 'junction'),
  n('l2_n4', -80, -150, 90, 'end', 'Face B'),
  n('l2_cross_1', 100, -150, 0, 'junction'),
  n('l2_cross_2', 120, -150, -100, 'end', 'Ventilation'),
  n('l3_n1', -40, -250, -40, 'junction'),
  n('l3_n2', -100, -260, -80, 'end', 'Extraction Point'),
  n('l3_n3', 60, -250, -20, 'junction'),
  n('l3_n4', 150, -280, -50, 'end', 'Deep Exploration'),
  n('ramp_s_l1_mid', 80, -25, 50, 'junction'),
  n('ramp_l1_l2_mid', 150, -100, 50, 'junction'),
];

const tunnels: MineTunnel[] = [
  t('t_shaft_1', 'surf_entry', 'shaft_l1', 'main_shaft', 8),
  t('t_shaft_2', 'shaft_l1', 'shaft_l2', 'main_shaft', 8),
  t('t_shaft_3', 'shaft_l2', 'shaft_l3', 'main_shaft', 8),
  t('t_shaft_4', 'shaft_l3', 'shaft_bottom', 'main_shaft', 6),
  t('t_l1_1', 'shaft_l1', 'l1_n1'),
  t('t_l1_2', 'l1_n1', 'l1_n2'),
  t('t_l1_3', 'shaft_l1', 'l1_n3'),
  t('t_l1_4', 'l1_n3', 'l1_n4'),
  t('t_l1_loop_1', 'shaft_l1', 'l1_loop_1'),
  t('t_l1_loop_2', 'l1_loop_1', 'l1_loop_2'),
  t('t_l1_loop_3', 'l1_loop_2', 'shaft_l1'),
  t('t_l2_1', 'shaft_l2', 'l2_n1'),
  t('t_l2_2', 'l2_n1', 'l2_n2'),
  t('t_l2_3', 'shaft_l2', 'l2_n3'),
  t('t_l2_4', 'l2_n3', 'l2_n4'),
  t('t_l2_5', 'shaft_l2', 'l2_cross_1'),
  t('t_l2_6', 'l2_cross_1', 'l2_cross_2'),
  t('t_l3_1', 'shaft_l3', 'l3_n1'),
  t('t_l3_2', 'l3_n1', 'l3_n2', 'ramp'),
  t('t_l3_3', 'shaft_l3', 'l3_n3'),
  t('t_l3_4', 'l3_n3', 'l3_n4', 'ramp'),
  t('t_ramp_1', 'surf_entry', 'ramp_s_l1_mid', 'ramp'),
  t('t_ramp_2', 'ramp_s_l1_mid', 'l1_n1', 'ramp'),
  t('t_ramp_3', 'l1_n1', 'ramp_l1_l2_mid', 'ramp'),
  t('t_ramp_4', 'ramp_l1_l2_mid', 'l2_cross_1', 'ramp'),
];

const levels: MineLevel[] = [
  { id: 'lvl_1', depth: -50, name: 'Level 1 - Logistics', color: '#0eb8c3' },
  { id: 'lvl_2', depth: -150, name: 'Level 2 - Production', color: '#f59e0b' },
  { id: 'lvl_3', depth: -250, name: 'Level 3 - Extraction', color: '#ef4444' },
];

export const mineLayout: MineLayout = {
  nodes,
  tunnels,
  levels,
  centerReference: {
    lat: CENTER_LAT,
    lng: CENTER_LNG
  }
};

