import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Settings, 
  Brain, 
  Server,
  Shield,
  CheckCircle,
  AlertCircle,
  Save,
  RefreshCw,
  TrendingUp,
  User,
  Calendar
} from 'lucide-react'
import { systemApi } from '@/api/system'
import { analysisApi } from '@/api/analysis'
import { healthCheck } from '@/api/index'
import { AnalysisConfig } from '@/api/types'
import { toast } from 'sonner'
import { UserPreferencesSettings } from '@/components/UserPreferencesSettings'
import { SchedulerStatus } from '@/components/SchedulerStatus'



export default function SettingsPage() {
  const [models, setModels] = useState<any>({})
  const [analysts, setAnalysts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [systemHealth, setSystemHealth] = useState<'healthy' | 'warning' | 'error'>('healthy')
  const [analysisConfig, setAnalysisConfig] = useState<AnalysisConfig | null>(null)
  const [modelFormData, setModelFormData] = useState({
    llm_provider: '',
    backend_url: '',
    shallow_thinker: '',
    deep_thinker: '',
    default_research_depth: 1,
    default_analysts: [] as string[]
  })

  useEffect(() => {
    loadModels()
    loadAnalysts()
    loadAnalysisConfig()
    checkSystemHealth()
  }, [])



  const loadModels = async () => {
    try {
      const response = await systemApi.getModels()
      setModels(response)
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }

  const loadAnalysts = async () => {
    try {
      const response = await systemApi.getAnalysts()
      setAnalysts(response.analysts || [])
    } catch (error) {
      console.error('Failed to load analysts:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadAnalysisConfig = async () => {
    try {
      const response = await analysisApi.getAnalysisConfig()
      const config = response.default_config
      setAnalysisConfig(config)
      
      // Also get system config to load user preferences including language settings
      const systemConfig = await systemApi.getConfig()
      const userPrefs = systemConfig.user_preferences || {}
      
      setModelFormData({
        llm_provider: config.llm_provider,
        backend_url: config.backend_url,
        shallow_thinker: config.shallow_thinker,
        deep_thinker: config.deep_thinker,
        default_research_depth: config.research_depth,
        default_analysts: config.analysts
      })
    } catch (error) {
      console.error('Failed to load analysis config:', error)
    }
  }

  const checkSystemHealth = async () => {
    try {
      await healthCheck()
      setSystemHealth('healthy')
    } catch (error) {
      setSystemHealth('error')
    }
  }



  const handleSaveModelConfig = async () => {
    setSaving(true)
    try {
      await systemApi.updateUserPreferences(modelFormData)
      toast.success('AI模型配置保存成功')
      loadAnalysisConfig()
    } catch (error) {
      console.error('Failed to save model config:', error)
      toast.error('保存AI模型配置失败')
    } finally {
      setSaving(false)
    }
  }



  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-2">
          <Settings className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">系统设置</h1>
        </div>
        <div className="grid gap-6">
          {[...Array(3)].map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="h-6 bg-gray-200 rounded animate-pulse" />
                <div className="h-4 bg-gray-200 rounded animate-pulse" />
              </CardHeader>
              <CardContent>
                <div className="h-20 bg-gray-200 rounded animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Settings className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">系统设置</h1>
        </div>
        <div className="flex items-center space-x-2">
          <Badge 
            variant={systemHealth === 'healthy' ? 'default' : 'destructive'}
            className={systemHealth === 'healthy' ? 'bg-green-100 text-green-700' : ''}
          >
            {systemHealth === 'healthy' ? (
              <CheckCircle className="h-3 w-3 mr-1" />
            ) : (
              <AlertCircle className="h-3 w-3 mr-1" />
            )}
            {systemHealth === 'healthy' ? '系统正常' : '系统异常'}
          </Badge>
          <Button variant="outline" size="sm" onClick={checkSystemHealth}>
            <RefreshCw className="h-4 w-4 mr-2" />
            检查状态
          </Button>
        </div>
      </div>

      <Tabs defaultValue="user-preferences" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="user-preferences" className="flex items-center space-x-2">
            <User className="h-4 w-4" />
            <span>用户偏好</span>
          </TabsTrigger>
          <TabsTrigger value="ai-models" className="flex items-center space-x-2">
            <Brain className="h-4 w-4" />
            <span>AI 模型</span>
          </TabsTrigger>
          <TabsTrigger value="scheduler" className="flex items-center space-x-2">
            <Calendar className="h-4 w-4" />
            <span>调度器</span>
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center space-x-2">
            <Server className="h-4 w-4" />
            <span>系统信息</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="flex items-center space-x-2">
            <Shield className="h-4 w-4" />
            <span>安全设置</span>
          </TabsTrigger>
        </TabsList>

        {/* User Preferences */}
        <TabsContent value="user-preferences" className="space-y-6">
          <UserPreferencesSettings />
        </TabsContent>

        {/* Scheduler Management */}
        <TabsContent value="scheduler" className="space-y-6">
          <SchedulerStatus showFullView={true} />
        </TabsContent>

        {/* AI Models Configuration */}
        <TabsContent value="ai-models" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>AI模型配置</CardTitle>
              <CardDescription>
                配置默认的AI模型和分析参数，所有新分析任务将使用这些设置
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="model-provider">LLM 提供商</Label>
                  <Select 
                    value={modelFormData.llm_provider} 
                    onValueChange={(value) => {
                      setModelFormData(prev => ({
                        ...prev, 
                        llm_provider: value,
                        backend_url: models[value]?.default_backend_url || '',
                        shallow_thinker: models[value]?.models?.[0] || '',
                        deep_thinker: models[value]?.models?.[0] || ''
                      }))
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择提供商" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="google">Google</SelectItem>
                      <SelectItem value="aliyun">阿里云</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="backend-url">API 后端地址</Label>
                  <Input
                    id="backend-url"
                    value={modelFormData.backend_url}
                    onChange={(e) => setModelFormData(prev => ({...prev, backend_url: e.target.value}))}
                    placeholder="API 后端地址"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="shallow-model">快速思考模型</Label>
                  <Select 
                    value={modelFormData.shallow_thinker} 
                    onValueChange={(value) => setModelFormData(prev => ({...prev, shallow_thinker: value}))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择模型" />
                    </SelectTrigger>
                    <SelectContent>
                      {models[modelFormData.llm_provider]?.models?.map((model: string) => (
                        <SelectItem key={model} value={model}>{model}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="deep-model">深度思考模型</Label>
                  <Select 
                    value={modelFormData.deep_thinker} 
                    onValueChange={(value) => setModelFormData(prev => ({...prev, deep_thinker: value}))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="选择模型" />
                    </SelectTrigger>
                    <SelectContent>
                      {models[modelFormData.llm_provider]?.models?.map((model: string) => (
                        <SelectItem key={model} value={model}>{model}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="default-depth">默认研究深度</Label>
                  <Select 
                    value={modelFormData.default_research_depth.toString()} 
                    onValueChange={(value) => setModelFormData(prev => ({...prev, default_research_depth: parseInt(value)}))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">浅层分析</SelectItem>
                      <SelectItem value="2">标准分析</SelectItem>
                      <SelectItem value="3">深度分析</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>默认分析师团队</Label>
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    {analysts.map((analyst) => (
                      <div
                        key={analyst.value}
                        className={`p-2 border rounded cursor-pointer transition-colors ${
                          modelFormData.default_analysts.includes(analyst.value)
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => {
                          setModelFormData(prev => ({
                            ...prev,
                            default_analysts: prev.default_analysts.includes(analyst.value)
                              ? prev.default_analysts.filter(a => a !== analyst.value)
                              : [...prev.default_analysts, analyst.value]
                          }))
                        }}
                      >
                        <div className="flex items-center space-x-2">
                          <TrendingUp className="h-3 w-3" />
                          <span className="text-xs font-medium">{analyst.label}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Language Settings Notice */}
              <div className="pt-6 border-t">
                <h4 className="font-medium mb-4">语言设置</h4>
                <Alert>
                  <User className="h-4 w-4" />
                  <AlertDescription>
                    AI报告的语言设置已统一移至"用户偏好"标签页。所有需要语言设置的功能（包括AI报告生成、界面显示等）都将使用用户偏好中的统一语言配置。
                  </AlertDescription>
                </Alert>
              </div>

              <div className="pt-4 border-t">
                <Button onClick={handleSaveModelConfig} disabled={saving}>
                  {saving ? (
                    <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4 mr-2" />
                  )}
                  保存AI模型配置
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>当前配置预览</CardTitle>
              <CardDescription>
                当前AI模型配置的详细信息
              </CardDescription>
            </CardHeader>
            <CardContent>
              {analysisConfig && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h5 className="font-medium mb-2">模型配置</h5>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">提供商:</span>
                          <Badge variant="outline">{analysisConfig.llm_provider}</Badge>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">快速模型:</span>
                          <Badge variant="outline">{analysisConfig.shallow_thinker}</Badge>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">深度模型:</span>
                          <Badge variant="outline">{analysisConfig.deep_thinker}</Badge>
                        </div>
                      </div>
                    </div>
                    <div>
                      <h5 className="font-medium mb-2">默认设置</h5>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">研究深度:</span>
                          <Badge variant="outline">级别 {analysisConfig.research_depth}</Badge>
                        </div>
                        <div className="text-sm">
                          <span className="text-gray-600">默认分析师:</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {analysisConfig.analysts.map((analyst: string) => (
                              <Badge key={analyst} variant="secondary" className="text-xs">
                                {analysts.find(a => a.value === analyst)?.label || analyst}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Information */}
        <TabsContent value="system" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>系统状态</CardTitle>
              <CardDescription>
                实时系统运行状态和性能指标
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">API 服务</span>
                    <Badge variant="default" className="bg-green-100 text-green-700">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      运行中
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">数据库连接</span>
                    <Badge variant="default" className="bg-green-100 text-green-700">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      正常
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">后台任务</span>
                    <Badge variant="default" className="bg-green-100 text-green-700">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      活跃
                    </Badge>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">系统版本</span>
                    <span className="text-sm text-gray-600">v1.0.0</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">API 版本</span>
                    <span className="text-sm text-gray-600">v1.0.0</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">最后更新</span>
                    <span className="text-sm text-gray-600">2024-08-23</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>安全设置</CardTitle>
              <CardDescription>
                系统安全配置和访问控制
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Alert>
                <Shield className="h-4 w-4" />
                <AlertDescription>
                  系统采用多层安全防护，包括 API 密钥加密存储、请求限流和访问日志记录。
                  所有敏感数据均经过加密处理，确保您的交易信息安全。
                </AlertDescription>
              </Alert>
              
              <div className="mt-6 space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">API 密钥加密</span>
                  <Badge variant="default" className="bg-green-100 text-green-700">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    已启用
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">请求限流</span>
                  <Badge variant="default" className="bg-green-100 text-green-700">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    已启用
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">访问日志</span>
                  <Badge variant="default" className="bg-green-100 text-green-700">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    已启用
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
