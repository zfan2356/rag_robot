import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Description as DocumentIcon,
  SmartToy as ModelIcon,
  Chat as PromptIcon,
} from '@mui/icons-material';
import { useState } from 'react';
import { Documents } from './pages/Documents';
import { Models } from './pages/Models';
import { Prompts } from './pages/Prompts';

const drawerWidth = 240;

const queryClient = new QueryClient();

function App() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <div>
      <Toolbar />
      <List>
        <ListItem button component={Link} to="/documents">
          <ListItemIcon>
            <DocumentIcon />
          </ListItemIcon>
          <ListItemText primary="文档管理" />
        </ListItem>
        <ListItem button component={Link} to="/models">
          <ListItemIcon>
            <ModelIcon />
          </ListItemIcon>
          <ListItemText primary="模型管理" />
        </ListItem>
        <ListItem button component={Link} to="/prompts">
          <ListItemIcon>
            <PromptIcon />
          </ListItemIcon>
          <ListItemText primary="提示词管理" />
        </ListItem>
      </List>
    </div>
  );

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Box sx={{ display: 'flex' }}>
          <CssBaseline />
          <AppBar
            position="fixed"
            sx={{
              width: { sm: `calc(100% - ${drawerWidth}px)` },
              ml: { sm: `${drawerWidth}px` },
            }}
          >
            <Toolbar>
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{ mr: 2, display: { sm: 'none' } }}
              >
                <MenuIcon />
              </IconButton>
              <Typography variant="h6" noWrap component="div">
                RAG Robot
              </Typography>
            </Toolbar>
          </AppBar>
          <Box
            component="nav"
            sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
          >
            <Drawer
              variant="temporary"
              open={mobileOpen}
              onClose={handleDrawerToggle}
              ModalProps={{
                keepMounted: true, // Better open performance on mobile.
              }}
              sx={{
                display: { xs: 'block', sm: 'none' },
                '& .MuiDrawer-paper': {
                  boxSizing: 'border-box',
                  width: drawerWidth,
                },
              }}
            >
              {drawer}
            </Drawer>
            <Drawer
              variant="permanent"
              sx={{
                display: { xs: 'none', sm: 'block' },
                '& .MuiDrawer-paper': {
                  boxSizing: 'border-box',
                  width: drawerWidth,
                },
              }}
              open
            >
              {drawer}
            </Drawer>
          </Box>
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              width: { sm: `calc(100% - ${drawerWidth}px)` },
            }}
          >
            <Toolbar />
            <Routes>
              <Route path="/documents" element={<Documents />} />
              <Route path="/models" element={<Models />} />
              <Route path="/prompts" element={<Prompts />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
