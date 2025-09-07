from enum import Enum

class UserRole(str, Enum):
    """用户角色枚举"""
    admin = 'admin'          
    customer = 'customer'
    others = 'others'       

class TaskStatus(str, Enum):
    """任务状态枚举"""
    pending = 'pending'      
    running = 'running'      
    completed = 'completed'  
    cancelled = 'cancelled'  

class ExpressStatus(str, Enum):
    """快递状态枚举"""
    unassigned = 'unassigned' 
    delivering = 'delivering'  
    completed = 'completed'    
    others = 'others'      

class CarTaskStatus(str, Enum):
    """小车任务状态枚举"""
    idle = 'idle'                  
    delivering = 'delivering'        
    maintenance = 'maintenance'      
    offline = 'offline'            
    others = 'others'               

class AppointmentStatus(str, Enum):
    """预约状态枚举"""
    scheduled = 'scheduled'   
    delivered = 'delivered'   
    cancelled = 'cancelled'    
