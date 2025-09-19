import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Clock, Globe, RotateCcw, Check, Settings2 } from 'lucide-react'
import { 
  getUserPreferences,
  setUserPreferences,
  resetUserPreferences,
  getDefaultPreferences,
  getSupportedLanguages,
  getCommonTimezones, 
  getTimezoneOffset,
  getLanguageDisplayName,
  detectUserLanguage,
  getUserTimeZone,
  type UserPreferences
} from '@/lib/utils'
import { systemApi } from '@/api/system'
import { toast } from 'sonner'

export function UserPreferencesSettings() {
  const [preferences, setPreferences] = useState<UserPreferences>(getUserPreferences())
  const [hasChanges, setHasChanges] = useState(false)
  const [saving, setSaving] = useState(false)

  const handlePreferenceChange = (key: keyof UserPreferences, value: string) => {
    const newPreferences = { ...preferences, [key]: value }
    setPreferences(newPreferences)
    setHasChanges(JSON.stringify(newPreferences) !== JSON.stringify(getUserPreferences()))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      // 保存到本地存储
      setUserPreferences(preferences)
      
      // 同步到后端API，统一语言设置
      await systemApi.updateUserPreferences({
        default_language: preferences.language,
        // 确保AI报告使用相同的语言设置
        report_language: preferences.language
      })
      
      setHasChanges(false)
      toast.success('偏好设置已保存并同步到服务器')
    } catch (error) {
      console.error('Failed to sync preferences to server:', error)
      toast.error('偏好设置已本地保存，但同步到服务器失败')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    const defaultPrefs = getDefaultPreferences()
    setPreferences(defaultPrefs)
    setHasChanges(true)
    toast.success('偏好设置已重置为自动检测值')
  }

  const handleCancel = () => {
    setPreferences(getUserPreferences())
    setHasChanges(false)
  }

  const currentPrefs = getUserPreferences()

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="h-5 w-5" />
          用户偏好设置
        </CardTitle>
        <CardDescription>
          配置系统语言、时区等个人偏好。语言设置将应用于AI报告生成、界面显示等所有功能，系统将自动检测浏览器设置作为默认值
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        {/* 当前设置显示 */}
        <div className="p-4 bg-gray-50 rounded-lg space-y-2">
          <div className="text-sm font-medium text-gray-700">当前设置</div>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-gray-500" />
              <span>系统语言: {getLanguageDisplayName(currentPrefs.language)}</span>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-gray-500" />
              <span>时区: {currentPrefs.timezone} ({getTimezoneOffset(currentPrefs.timezone)})</span>
            </div>
          </div>
        </div>

        {/* 语言设置 */}
        <div className="space-y-3">
          <div>
            <Label htmlFor="language-select" className="flex items-center gap-2">
              <Globe className="h-4 w-4" />
              系统语言
            </Label>
            <div className="text-xs text-gray-500 mt-1">
              自动检测: {getLanguageDisplayName(detectUserLanguage())} (基于浏览器设置)
            </div>
          </div>
          
          <Select 
            value={preferences.language} 
            onValueChange={(value) => handlePreferenceChange('language', value)}
          >
            <SelectTrigger id="language-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {getSupportedLanguages().map((lang) => (
                <SelectItem key={lang.value} value={lang.value}>
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span>{lang.nativeLabel}</span>
                      {lang.isDefault && (
                        <span className="text-xs text-blue-600 bg-blue-100 px-1 rounded">默认</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">{lang.description}</div>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Separator />

        {/* 时区设置 */}
        <div className="space-y-3">
          <div>
            <Label htmlFor="timezone-select" className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              时区设置
            </Label>
            <div className="text-xs text-gray-500 mt-1">
              自动检测: {getUserTimeZone()} ({getTimezoneOffset(getUserTimeZone())}) (基于设备位置)
            </div>
          </div>
          
          <Select 
            value={preferences.timezone} 
            onValueChange={(value) => handlePreferenceChange('timezone', value)}
          >
            <SelectTrigger id="timezone-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {getCommonTimezones().map((tz) => (
                <SelectItem key={tz.value} value={tz.value}>
                  <div className="flex items-center justify-between w-full">
                    <span>{tz.label}</span>
                    <span className="text-xs text-gray-500 ml-2">{tz.offset}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* 预览变更 */}
        {hasChanges && (
          <>
            <Separator />
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg space-y-2">
              <div className="text-sm font-medium text-blue-800">预览新设置</div>
              <div className="space-y-1 text-sm text-blue-700">
                {preferences.language !== currentPrefs.language && (
                  <div className="flex items-center gap-2">
                    <Globe className="h-3 w-3" />
                    <span>系统语言: {getLanguageDisplayName(preferences.language)}</span>
                  </div>
                )}
                {preferences.timezone !== currentPrefs.timezone && (
                  <div className="flex items-center gap-2">
                    <Clock className="h-3 w-3" />
                    <span>时区: {preferences.timezone} ({getTimezoneOffset(preferences.timezone)})</span>
                  </div>
                )}
              </div>
              {preferences.timezone !== currentPrefs.timezone && (
                <div className="text-xs text-blue-600 mt-1">
                  示例：任务将在 09:00 ({getTimezoneOffset(preferences.timezone)}) 执行
                </div>
              )}
            </div>
          </>
        )}

        {/* 操作按钮 */}
        <div className="flex gap-2 pt-4 border-t">
          <Button 
            onClick={handleSave} 
            disabled={!hasChanges || saving}
            className="flex items-center gap-2"
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                同步中...
              </>
            ) : (
              <>
                <Check className="h-4 w-4" />
                保存设置
              </>
            )}
          </Button>
          
          <Button 
            variant="outline" 
            onClick={handleReset}
            className="flex items-center gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            重置为自动检测
          </Button>
          
          {hasChanges && (
            <Button variant="ghost" onClick={handleCancel}>
              取消
            </Button>
          )}
        </div>

        {/* 说明信息 */}
        <div className="text-xs text-gray-500 space-y-1 pt-2 border-t">
          <div className="font-medium mb-2">说明:</div>
          <div>• <strong>系统语言</strong>：控制AI生成报告、界面显示等所有需要语言设置的功能，统一替换了原有分散的语言配置</div>
          <div>• <strong>时区设置</strong>：影响所有时间显示和新创建任务的执行时间</div>
          <div>• <strong>自动检测</strong>：系统根据浏览器设置自动识别最佳配置</div>
          <div>• <strong>已存在任务</strong>：保持创建时的时区设置不变</div>
        </div>
      </CardContent>
    </Card>
  )
}
