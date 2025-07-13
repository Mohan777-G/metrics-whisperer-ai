import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AlertCircle, Database, MessageSquare, TrendingUp, Clock, ExternalLink } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';

interface QueryResponse {
  natural_language_response: string;
  promql_query: string;
  raw_data: any;
  grafana_url?: string;
  execution_time: number;
}

const Index = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  // Fix environment variable access for browser
  const getApiUrl = () => {
    return import.meta.env.VITE_API_URL || 'http://localhost:8000';
  };

  const exampleQueries = [
    "What's the average CPU usage?",
    "Show me the request rate",
    "What's the current memory usage?",
    "What's the error rate?",
    "Show me request latency",
    "Is the system up?"
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const apiUrl = getApiUrl();
      const res = await fetch(`${apiUrl}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Query failed');
      }

      const data: QueryResponse = await res.json();
      setResponse(data);
      
      toast({
        title: "Query successful!",
        description: `Executed in ${(data.execution_time * 1000).toFixed(0)}ms`,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      setError(errorMessage);
      toast({
        title: "Query failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExampleClick = (exampleQuery: string) => {
    setQuery(exampleQuery);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Database className="h-8 w-8 text-purple-400" />
            <h1 className="text-4xl font-bold text-white">AI Prometheus Agent</h1>
          </div>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            Ask questions about your metrics in natural language. I'll translate them to PromQL and get you answers.
          </p>
        </div>

        {/* Query Form */}
        <Card className="max-w-4xl mx-auto mb-8 bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <MessageSquare className="h-5 w-5" />
              Ask Your Question
            </CardTitle>
            <CardDescription className="text-slate-400">
              Type a natural language query about your metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="query" className="text-slate-200">Your Question</Label>
                <Input
                  id="query"
                  type="text"
                  placeholder="e.g., What's the average CPU usage over the last 5 minutes?"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white placeholder-slate-400"
                  disabled={loading}
                />
              </div>
              <Button 
                type="submit" 
                disabled={loading || !query.trim()}
                className="w-full bg-purple-600 hover:bg-purple-700"
              >
                {loading ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Analyzing...
                  </div>
                ) : (
                  'Ask Question'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Example Queries */}
        <Card className="max-w-4xl mx-auto mb-8 bg-slate-800 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white">Try These Examples</CardTitle>
            <CardDescription className="text-slate-400">
              Click on any example to try it out
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
              {exampleQueries.map((example, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleExampleClick(example)}
                  className="justify-start text-left h-auto p-3 bg-slate-700 border-slate-600 text-slate-200 hover:bg-slate-600"
                  disabled={loading}
                >
                  {example}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Alert className="max-w-4xl mx-auto mb-8 bg-red-900 border-red-700">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-red-100">
              {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Response Display */}
        {response && (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Natural Language Response */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-white">
                  <MessageSquare className="h-5 w-5 text-green-400" />
                  Answer
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-200 text-lg leading-relaxed">
                  {response.natural_language_response}
                </p>
              </CardContent>
            </Card>

            {/* Technical Details */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* PromQL Query */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-white">
                    <Database className="h-5 w-5 text-blue-400" />
                    PromQL Query
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-slate-900 p-4 rounded-lg border border-slate-600">
                    <code className="text-green-400 font-mono text-sm break-all">
                      {response.promql_query}
                    </code>
                  </div>
                </CardContent>
              </Card>

              {/* Execution Info */}
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-white">
                    <Clock className="h-5 w-5 text-yellow-400" />
                    Execution Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Execution Time:</span>
                    <Badge variant="secondary" className="bg-slate-700 text-slate-200">
                      {(response.execution_time * 1000).toFixed(0)}ms
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Data Points:</span>
                    <Badge variant="secondary" className="bg-slate-700 text-slate-200">
                      {response.raw_data?.result?.length || 0}
                    </Badge>
                  </div>
                  {response.grafana_url && (
                    <div className="pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        asChild
                        className="w-full bg-slate-700 border-slate-600 text-slate-200 hover:bg-slate-600"
                      >
                        <a 
                          href={response.grafana_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2"
                        >
                          <TrendingUp className="h-4 w-4" />
                          View in Grafana
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Raw Data (Collapsible) */}
            {response.raw_data?.result && response.raw_data.result.length > 0 && (
              <Card className="bg-slate-800 border-slate-700">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-white">
                    <Database className="h-5 w-5 text-purple-400" />
                    Raw Data
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    Detailed metrics data from Prometheus
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-slate-900 p-4 rounded-lg border border-slate-600 max-h-96 overflow-auto">
                    <pre className="text-slate-300 text-sm">
                      {JSON.stringify(response.raw_data, null, 2)}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 text-slate-400">
          <p>Powered by FastAPI, Prometheus, and AI • Built with ❤️ for DevOps</p>
        </div>
      </div>
    </div>
  );
};

export default Index;
