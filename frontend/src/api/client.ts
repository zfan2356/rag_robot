import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000'; // 修改为正确的API路径，移除/api前缀

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
});

// 请求拦截器
apiClient.interceptors.request.use(
    (config) => {
        // 添加时间戳防止缓存
        if (config.method === 'get') {
            config.params = {
                ...config.params,
                _t: Date.now()
            };
        }
        console.log('Request:', config.method?.toUpperCase(), config.url, config.params);
        return config;
    },
    (error) => {
        console.error('Request Error:', error);
        return Promise.reject(error);
    }
);

// 响应拦截器
apiClient.interceptors.response.use(
    (response) => {
        console.log('Response:', response.status, response.data);
        return response;
    },
    (error) => {
        if (error.response) {
            // 服务器返回了错误状态码
            console.error('API Error:', error.response.status, error.response.data);
        } else if (error.request) {
            // 请求已发出，但没有收到响应
            console.error('API Error: No response received', error.request);
        } else {
            // 请求配置出错
            console.error('API Error:', error.message);
        }
        return Promise.reject(error);
    }
);
