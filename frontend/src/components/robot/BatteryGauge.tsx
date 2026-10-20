/**
 * Copyright (c) 2026 TOYOTA MOTOR CORPORATION. ALL RIGHTS RESERVED.
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { Box, LinearProgress } from '@mui/material';

const BatteryGauge = ({ level }: { level: number }) => {
  return (
    <Box sx={{ width: '100%'}}>
      <LinearProgress
        variant="determinate"
        value={level ? level : 0}
        sx={{
          height: 20,
          borderRadius: 5,
          backgroundColor: '#eee',
          '& .MuiLinearProgress-bar': {
            backgroundColor: level < 20 ? 'red' : level < 50 ? 'orange' : 'green',
          },
        }}
      />
    </Box>
  );
};

export default BatteryGauge;