export interface MatrixUser {
  id: string;
  name: string;
}

export interface MatrixCell {
  x: string;
  y: string;
  status: 'congruent' | 'missed' | 'unnecessary';
  value: number;
}

export interface STCMatrixResponse {
  users: MatrixUser[];
  matrix: MatrixCell[];
  stc_value: number;
}
