import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { RequireAuth } from './RequireAuth';

// Pages
import LandingPage from '@/pages/LandingPage';
import SignupPage from '@/pages/SignupPage';
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import SellerPage from '@/pages/SellerPage';
import ProfilePage from '@/pages/ProfilePage';
import OrderHistoryPage from '@/pages/OrderHistoryPage';
import WishlistPage from '@/pages/WishlistPage';
import NotFoundPage from '@/pages/NotFoundPage';

export const AppRoutes = () => {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<MainLayout><LandingPage /></MainLayout>} />
      <Route path="/signup" element={<MainLayout><SignupPage /></MainLayout>} />
      <Route path="/login" element={<MainLayout><LoginPage /></MainLayout>} />
      {/* <Route path="/dashboard" element={<MainLayout><DashboardPage /></MainLayout>} />
      <Route path="/seller" element={<MainLayout><SellerPage /></MainLayout>} />
      <Route path="/profile" element={<MainLayout><ProfilePage /></MainLayout>} />
      <Route path="/orders" element={<MainLayout><OrderHistoryPage /></MainLayout>} />
      <Route path="/wishlist" element={<MainLayout><WishlistPage /></MainLayout>} /> */}
      
      {/* Protected routes */}
      <Route 
        path="/dashboard" 
        element={
          <RequireAuth>
            <MainLayout><DashboardPage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/seller" 
        element={
          <RequireAuth>
            <MainLayout><SellerPage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/profile" 
        element={
          <RequireAuth>
            <MainLayout><ProfilePage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/orders" 
        element={
          <RequireAuth>
            <MainLayout><OrderHistoryPage /></MainLayout>
          </RequireAuth>
        } 
      />
      <Route 
        path="/wishlist" 
        element={
          <RequireAuth>
            <MainLayout><WishlistPage /></MainLayout>
          </RequireAuth>
        } 
      />
      
      {/* Catch all route */}
      <Route path="*" element={<MainLayout><NotFoundPage /></MainLayout>} />
    </Routes>
  );
};