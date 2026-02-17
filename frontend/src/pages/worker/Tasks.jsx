import React, { useState, useEffect } from 'react';
import Layout from '../../components/Layout';
import { taskAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Loader2, ClipboardList, Calendar, CheckCircle, Clock, AlertTriangle } from 'lucide-react';
import { formatDateTime, getStatusColor } from '../../lib/utils';
import { toast } from 'sonner';

export default function TasksPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      const response = await taskAPI.getAll();
      setTasks(response.data);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
      toast.error('Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleStatusUpdate = async (taskId, newStatus) => {
    try {
      await taskAPI.update(taskId, { status: newStatus });
      toast.success('Task updated successfully');
      fetchTasks();
    } catch (error) {
      console.error('Failed to update task:', error);
      toast.error('Failed to update task');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'IN_PROGRESS':
        return <Clock className="h-5 w-5 text-blue-600" />;
      case 'OVERDUE':
        return <AlertTriangle className="h-5 w-5 text-red-600" />;
      default:
        return <ClipboardList className="h-5 w-5 text-yellow-600" />;
    }
  };

  const pendingTasks = tasks.filter(t => t.status === 'PENDING' || t.status === 'IN_PROGRESS');
  const completedTasks = tasks.filter(t => t.status === 'COMPLETED');

  return (
    <Layout>
      <div className="space-y-6" data-testid="tasks-page">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold font-['Barlow_Condensed'] tracking-tight">
            My Tasks
          </h1>
          <p className="text-zinc-500 mt-1">
            {pendingTasks.length} pending, {completedTasks.length} completed
          </p>
        </div>

        {/* Tasks List */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : tasks.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-64 text-center">
              <ClipboardList className="h-12 w-12 text-zinc-300 mb-4" />
              <p className="text-zinc-500">No tasks assigned</p>
              <p className="text-sm text-zinc-400">Tasks will appear here when assigned by admin</p>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Pending Tasks */}
            {pendingTasks.length > 0 && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold font-['Barlow_Condensed']">
                  Active Tasks ({pendingTasks.length})
                </h2>
                <div className="space-y-3">
                  {pendingTasks.map((task) => (
                    <Card key={task.id} className="card-interactive">
                      <CardContent className="p-4">
                        <div className="flex items-start gap-4">
                          <div className="p-2 bg-zinc-100 rounded-lg">
                            {getStatusIcon(task.status)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2 mb-2">
                              <h3 className="font-semibold">{task.title}</h3>
                              <Badge className={getStatusColor(task.status)}>
                                {task.status}
                              </Badge>
                            </div>
                            {task.description && (
                              <p className="text-sm text-zinc-600 mb-2">{task.description}</p>
                            )}
                            {task.due_date && (
                              <div className="flex items-center gap-2 text-sm text-zinc-500">
                                <Calendar className="h-4 w-4" />
                                Due: {formatDateTime(task.due_date)}
                              </div>
                            )}
                            
                            {/* Status Update */}
                            <div className="mt-4 flex items-center gap-2">
                              <span className="text-sm text-zinc-500">Update status:</span>
                              <Select
                                value={task.status}
                                onValueChange={(value) => handleStatusUpdate(task.id, value)}
                              >
                                <SelectTrigger className="w-40" data-testid={`task-status-${task.id}`}>
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="PENDING">Pending</SelectItem>
                                  <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                                  <SelectItem value="COMPLETED">Completed</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Completed Tasks */}
            {completedTasks.length > 0 && (
              <div className="space-y-4">
                <h2 className="text-lg font-semibold font-['Barlow_Condensed'] text-zinc-600">
                  Completed ({completedTasks.length})
                </h2>
                <div className="space-y-3">
                  {completedTasks.map((task) => (
                    <Card key={task.id} className="bg-zinc-50">
                      <CardContent className="p-4">
                        <div className="flex items-start gap-4">
                          <div className="p-2 bg-green-100 rounded-lg">
                            <CheckCircle className="h-5 w-5 text-green-600" />
                          </div>
                          <div className="flex-1">
                            <h3 className="font-medium text-zinc-600">{task.title}</h3>
                            <p className="text-sm text-zinc-500">
                              Completed: {formatDateTime(task.completed_at)}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </Layout>
  );
}
