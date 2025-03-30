import React from 'react';
import { Box } from '@mui/material';

export const GradioEmbed: React.FC = () => {
    return (
        <Box sx={{
            width: '100%',
            height: 'calc(100vh - 64px)', // 减去顶部导航栏的高度
            border: 'none',
            overflow: 'hidden'
        }}>
            <iframe
                src="http://0.0.0.0:7860"
                style={{
                    width: '100%',
                    height: '100%',
                    border: 'none',
                }}
                title="Gradio Interface"
            />
        </Box>
    );
};
