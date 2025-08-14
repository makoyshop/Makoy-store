import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Textarea } from "./components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Avatar, AvatarFallback } from "./components/ui/avatar";
import { Separator } from "./components/ui/separator";
import { ShoppingCart, Wallet, CreditCard, MessageSquare, BookOpen, Plus, CheckCircle, XCircle, Clock, User, Settings, LogOut } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();
const useAuth = () => useContext(AuthContext);

// Auth Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUserData();
    }
  }, [token]);

  const fetchUserData = async () => {
    try {
      const response = await axios.get(`${API}/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user data:', error);
      logout();
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/login`, { email, password });
      const { access_token, user: userData } = response.data;
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      return false;
    }
  };

  const register = async (email, username, password, isAdmin = false) => {
    try {
      const response = await axios.post(`${API}/register`, {
        email,
        username,
        password,
        is_admin: isAdmin
      });
      const { access_token, user: userData } = response.data;
      setToken(access_token);
      setUser(userData);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      return true;
    } catch (error) {
      console.error('Registration failed:', error);
      return false;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, fetchUserData }}>
      {children}
    </AuthContext.Provider>
  );
};

// Header Component
const Header = () => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold">DigitalStore</h1>
          </div>
          
          {user && (
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2 bg-white/20 px-3 py-1 rounded-full">
                <Wallet className="h-4 w-4" />
                <span className="font-medium">{user.wallet_balance.toFixed(2)} Coins</span>
              </div>
              <div className="flex items-center space-x-2">
                <Avatar>
                  <AvatarFallback>{user.username.charAt(0).toUpperCase()}</AvatarFallback>
                </Avatar>
                <span className="font-medium">{user.username}</span>
                {user.is_admin && <Badge variant="secondary">Admin</Badge>}
              </div>
              <Button onClick={logout} variant="ghost" size="sm">
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

// Auth Component
const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    let success;
    if (isLogin) {
      success = await login(email, password);
    } else {
      success = await register(email, username, password, isAdmin);
    }
    
    if (success) {
      // Clear form
      setEmail('');
      setUsername('');
      setPassword('');
      setIsAdmin(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">
            {isLogin ? 'Login' : 'Register'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="username">Username</Label>
                <Input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {!isLogin && (
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="isAdmin"
                  checked={isAdmin}
                  onChange={(e) => setIsAdmin(e.target.checked)}
                />
                <Label htmlFor="isAdmin">Admin Account</Label>
              </div>
            )}
            
            <Button type="submit" className="w-full">
              {isLogin ? 'Login' : 'Register'}
            </Button>
          </form>
          
          <div className="mt-4 text-center">
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-indigo-600 hover:underline"
            >
              {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Products Component
const Products = () => {
  const [products, setProducts] = useState([]);
  const { user } = useAuth();

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  const purchaseProduct = async (productId) => {
    try {
      await axios.post(`${API}/purchase/${productId}`);
      alert('Purchase successful!');
      window.location.reload(); // Refresh to update wallet balance
    } catch (error) {
      alert(error.response?.data?.detail || 'Purchase failed');
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {products.map((product) => (
        <Card key={product.id} className="hover:shadow-lg transition-all duration-300 border-0 bg-white/90 backdrop-blur-sm">
          <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 rounded-t-lg flex items-center justify-center">
            {product.image_url ? (
              <img 
                src={product.image_url} 
                alt={product.name}
                className="w-full h-full object-cover rounded-t-lg"
              />
            ) : (
              <div className="text-gray-400">No Image</div>
            )}
          </div>
          <CardContent className="p-4">
            <h3 className="font-semibold text-lg mb-2">{product.name}</h3>
            <p className="text-gray-600 text-sm mb-3">{product.description}</p>
            <div className="flex items-center justify-between">
              <Badge variant="secondary">{product.category}</Badge>
              <span className="font-bold text-lg">{product.price} Coins</span>
            </div>
            <Button 
              className="w-full mt-3"
              onClick={() => purchaseProduct(product.id)}
              disabled={!user || user.wallet_balance < product.price}
            >
              <ShoppingCart className="h-4 w-4 mr-2" />
              {user && user.wallet_balance < product.price ? 'Insufficient Balance' : 'Buy Now'}
            </Button>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// TopUp Component
const TopUp = () => {
  const [amount, setAmount] = useState('');
  const [receiptFile, setReceiptFile] = useState(null);
  const [requests, setRequests] = useState([]);
  const { fetchUserData } = useAuth();

  useEffect(() => {
    fetchTopUpRequests();
  }, []);

  const fetchTopUpRequests = async () => {
    try {
      const response = await axios.get(`${API}/topup-requests`);
      setRequests(response.data);
    } catch (error) {
      console.error('Failed to fetch requests:', error);
    }
  };

  const handleFileChange = (e) => {
    setReceiptFile(e.target.files[0]);
  };

  const convertToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result);
      reader.onerror = error => reject(error);
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!receiptFile || !amount) return;

    try {
      const receiptData = await convertToBase64(receiptFile);
      await axios.post(`${API}/topup`, {
        amount: parseFloat(amount),
        receipt_data: receiptData
      });
      
      alert('Top-up request submitted successfully!');
      setAmount('');
      setReceiptFile(null);
      e.target.reset();
      fetchTopUpRequests();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to submit request');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <CreditCard className="h-5 w-5 mr-2" />
            Request Top-Up
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="amount">Amount (Coins)</Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="receipt">Receipt/Proof of Payment</Label>
              <Input
                id="receipt"
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                required
              />
            </div>
            
            <Button type="submit" className="w-full">
              Submit Request
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top-Up History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {requests.map((request) => (
              <div key={request.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-medium">{request.amount} Coins</div>
                  <div className="text-sm text-gray-500">
                    {new Date(request.created_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(request.status)}
                  <Badge variant={request.status === 'approved' ? 'default' : request.status === 'rejected' ? 'destructive' : 'secondary'}>
                    {request.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Admin Panel Component
const AdminPanel = () => {
  const [topupRequests, setTopupRequests] = useState([]);
  const [products, setProducts] = useState([]);
  const [newProduct, setNewProduct] = useState({
    name: '',
    description: '',
    price: '',
    image_url: '',
    category: ''
  });

  useEffect(() => {
    fetchTopupRequests();
    fetchAllProducts();
  }, []);

  const fetchTopupRequests = async () => {
    try {
      const response = await axios.get(`${API}/admin/topup-requests`);
      setTopupRequests(response.data);
    } catch (error) {
      console.error('Failed to fetch requests:', error);
    }
  };

  const fetchAllProducts = async () => {
    try {
      const response = await axios.get(`${API}/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  const handleApprove = async (requestId) => {
    try {
      await axios.post(`${API}/admin/topup-requests/${requestId}/approve`);
      alert('Request approved!');
      fetchTopupRequests();
    } catch (error) {
      alert('Failed to approve request');
    }
  };

  const handleReject = async (requestId) => {
    const notes = prompt('Rejection reason (optional):');
    try {
      await axios.post(`${API}/admin/topup-requests/${requestId}/reject`, null, {
        params: { admin_notes: notes || '' }
      });
      alert('Request rejected!');
      fetchTopupRequests();
    } catch (error) {
      alert('Failed to reject request');
    }
  };

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/products`, {
        ...newProduct,
        price: parseFloat(newProduct.price)
      });
      alert('Product created successfully!');
      setNewProduct({ name: '', description: '', price: '', image_url: '', category: '' });
      fetchAllProducts();
    } catch (error) {
      alert('Failed to create product');
    }
  };

  return (
    <Tabs defaultValue="topups" className="space-y-4">
      <TabsList>
        <TabsTrigger value="topups">Top-Up Requests</TabsTrigger>
        <TabsTrigger value="products">Manage Products</TabsTrigger>
      </TabsList>
      
      <TabsContent value="topups">
        <Card>
          <CardHeader>
            <CardTitle>Pending Top-Up Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topupRequests.filter(r => r.status === 'pending').map((request) => (
                <div key={request.id} className="border rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <div className="font-semibold">User: {request.user_id}</div>
                      <div>Amount: {request.amount} Coins</div>
                      <div className="text-sm text-gray-500">
                        {new Date(request.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <Button size="sm" onClick={() => handleApprove(request.id)}>
                        Approve
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleReject(request.id)}>
                        Reject
                      </Button>
                    </div>
                  </div>
                  {request.receipt_data && (
                    <div>
                      <Label>Receipt:</Label>
                      <img 
                        src={request.receipt_data} 
                        alt="Receipt" 
                        className="mt-2 max-w-xs max-h-48 object-contain border rounded"
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="products">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Add New Product</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateProduct} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Name</Label>
                    <Input
                      value={newProduct.name}
                      onChange={(e) => setNewProduct({...newProduct, name: e.target.value})}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Category</Label>
                    <Input
                      value={newProduct.category}
                      onChange={(e) => setNewProduct({...newProduct, category: e.target.value})}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea
                    value={newProduct.description}
                    onChange={(e) => setNewProduct({...newProduct, description: e.target.value})}
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Price (Coins)</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={newProduct.price}
                      onChange={(e) => setNewProduct({...newProduct, price: e.target.value})}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Image URL</Label>
                    <Input
                      value={newProduct.image_url}
                      onChange={(e) => setNewProduct({...newProduct, image_url: e.target.value})}
                    />
                  </div>
                </div>
                <Button type="submit">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Product
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </TabsContent>
    </Tabs>
  );
};

// Main Dashboard Component
const Dashboard = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('products');

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome back, {user?.username}!
          </h2>
          <p className="text-gray-600">Explore our digital marketplace</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="products" className="flex items-center space-x-2">
              <ShoppingCart className="h-4 w-4" />
              <span>Products</span>
            </TabsTrigger>
            <TabsTrigger value="wallet" className="flex items-center space-x-2">
              <Wallet className="h-4 w-4" />
              <span>Wallet</span>
            </TabsTrigger>
            <TabsTrigger value="support" className="flex items-center space-x-2">
              <MessageSquare className="h-4 w-4" />
              <span>Support</span>
            </TabsTrigger>
            <TabsTrigger value="blog" className="flex items-center space-x-2">
              <BookOpen className="h-4 w-4" />
              <span>Blog</span>
            </TabsTrigger>
            {user?.is_admin && (
              <TabsTrigger value="admin" className="flex items-center space-x-2">
                <Settings className="h-4 w-4" />
                <span>Admin</span>
              </TabsTrigger>
            )}
          </TabsList>

          <TabsContent value="products">
            <Products />
          </TabsContent>

          <TabsContent value="wallet">
            <TopUp />
          </TabsContent>

          <TabsContent value="support">
            <Card>
              <CardHeader>
                <CardTitle>Support Center</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Support ticket system coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="blog">
            <Card>
              <CardHeader>
                <CardTitle>Blog Posts</CardTitle>
              </CardHeader>
              <CardContent>
                <p>Blog posts coming soon...</p>
              </CardContent>
            </Card>
          </TabsContent>

          {user?.is_admin && (
            <TabsContent value="admin">
              <AdminPanel />
            </TabsContent>
          )}
        </Tabs>
      </div>
    </div>
  );
};

// Main App
function App() {
  const { user } = useAuth();

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route 
            path="/" 
            element={user ? <Dashboard /> : <Auth />} 
          />
          <Route 
            path="/auth" 
            element={user ? <Navigate to="/" /> : <Auth />} 
          />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default function AppWithAuth() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}