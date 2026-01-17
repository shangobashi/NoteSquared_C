import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChevronDown, ChevronUp, Copy, Check, Edit2, X, RotateCcw } from 'lucide-react';
import Button from './Button';
import Card from './Card';
import { Output, outputsApi } from '../services/api';

interface OutputCardProps {
  output: Output;
  onUpdate?: (output: Output) => void;
}

const outputTypeLabels: Record<string, { title: string; icon: string }> = {
  STUDENT_RECAP: { title: 'Student Recap', icon: '📝' },
  PRACTICE_PLAN: { title: 'Practice Plan', icon: '📅' },
  PARENT_EMAIL: { title: 'Parent Email', icon: '✉️' },
};

export default function OutputCard({ output, onUpdate }: OutputCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(output.content);
  const [isCopied, setIsCopied] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const config = outputTypeLabels[output.output_type] || { title: output.output_type, icon: '📄' };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(output.content);
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);

    // Mark as shared
    try {
      await outputsApi.share(output.id);
    } catch (e) {
      console.error('Failed to mark as shared', e);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const { data } = await outputsApi.update(output.id, editContent);
      onUpdate?.(data);
      setIsEditing(false);
    } catch (e) {
      console.error('Failed to save', e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRevert = async () => {
    try {
      const { data } = await outputsApi.revert(output.id);
      onUpdate?.(data);
      setEditContent(data.content);
    } catch (e) {
      console.error('Failed to revert', e);
    }
  };

  return (
    <Card className="overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-dark-border/20 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.icon}</span>
          <div>
            <h3 className="font-semibold text-dark-text-primary">{config.title}</h3>
            {output.is_edited && (
              <span className="text-xs text-brand">Edited</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {output.is_shared && (
            <span className="text-xs text-emerald-500">Shared</span>
          )}
          {isExpanded ? (
            <ChevronUp className="text-dark-text-secondary" size={20} />
          ) : (
            <ChevronDown className="text-dark-text-secondary" size={20} />
          )}
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="border-t border-dark-border">
          {/* Actions */}
          <div className="flex items-center justify-end gap-2 p-3 border-b border-dark-border bg-dark-bg/50">
            {!isEditing ? (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopy();
                  }}
                >
                  {isCopied ? (
                    <>
                      <Check size={16} className="mr-1" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy size={16} className="mr-1" />
                      Copy
                    </>
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsEditing(true);
                    setEditContent(output.content);
                  }}
                >
                  <Edit2 size={16} className="mr-1" />
                  Edit
                </Button>
                {output.is_edited && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRevert();
                    }}
                  >
                    <RotateCcw size={16} className="mr-1" />
                    Revert
                  </Button>
                )}
              </>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsEditing(false);
                    setEditContent(output.content);
                  }}
                >
                  <X size={16} className="mr-1" />
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSave();
                  }}
                  isLoading={isSaving}
                >
                  Save
                </Button>
              </>
            )}
          </div>

          {/* Content Area */}
          <div className="p-4">
            {isEditing ? (
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-96 p-4 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand"
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              <div className="markdown-content prose prose-invert max-w-none">
                <ReactMarkdown>{output.content}</ReactMarkdown>
              </div>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
