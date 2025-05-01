"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { useAuth } from "@/utils/auth";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
// import { Checkbox } from "@/components/ui/checkbox";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Flex } from "@radix-ui/themes";
import GoogleLogin, {
  NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID,
} from "@/components/auth/GoogleLogin";

const formSchema = z.object({
  email: z.string().email({
    message: "Please enter a valid email address.",
  }),
  password: z.string().min(4, {
    message: "Password must be at least 4 characters long.",
  }),
  rememberMe: z.boolean().default(false).optional(),
});

export default function LoginPage() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
      rememberMe: false,
    },
    mode: "onChange",
  });

  const { login, loginGoogle, loginError } = useAuth();

  function onSubmit(values: z.infer<typeof formSchema>) {
    login(values.email, values.password);
  }

  const handleGoogleLogin = (
    response: google.accounts.id.CredentialResponse
  ) => {
    loginGoogle({
      client_id: NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID,
      credential: response.credential,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-purple-50 to-blue-100 p-4">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
        key="login-form-container"
      >
        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">
              Welcome back
            </CardTitle>
            <CardDescription className="text-center">
              Enter your email and password to login
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex justify-between h-5">
                        <FormLabel>Email</FormLabel>
                        <FormMessage />
                      </div>
                      <FormControl>
                        <Input placeholder="you@example.com" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex justify-between h-5">
                        <FormLabel>Password</FormLabel>
                        <div className="min-h-[20px]">
                          <FormMessage />
                        </div>
                      </div>
                      <FormControl>
                        <Input
                          type="password"
                          placeholder="••••••••"
                          {...field}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <div className="flex items-center justify-between">
                  {/* <FormField
                    control={form.control}
                    name="rememberMe"
                    render={({ field }) => (
                      <FormItem className="flex flex-row items-center space-x-3 space-y-0">
                        <FormControl>
                          <Checkbox
                            checked={field.value}
                            onCheckedChange={field.onChange}
                          />
                        </FormControl>
                        <div className="space-y-1 leading-none">
                          <FormLabel>Remember me</FormLabel>
                        </div>
                      </FormItem>
                    )}
                  /> */}
                  <Link
                    href="/forgot-password"
                    className="text-sm text-primary hover:underline"
                  >
                    Forgot password?
                  </Link>
                </div>
                <Button type="submit" className="w-full">
                  Sign in
                </Button>

                {/* Render loginError if it exists */}
                <FormMessage>
                  <span className="text-red-500">
                    {loginError ? loginError : "\u00A0"}
                  </span>
                </FormMessage>
              </form>
            </Form>
            <Flex direction="column" align="center" justify="center">
              <p className="pb-4 text-sm text-white-700">or</p>
              <div className="min-h-[20px]">
                <GoogleLogin
                  type="signin_with"
                  handleCredentialResponse={handleGoogleLogin}
                />
              </div>
            </Flex>
          </CardContent>
          <CardFooter className="flex justify-center">
            <p className="text-sm text-muted-foreground">
              {"Don't have an account? "}
              <Link
                href={{
                  pathname: "/register",
                  query: {
                    sourcePage:
                      typeof window !== "undefined"
                        ? new URLSearchParams(window.location.search).get(
                            "sourcePage"
                          )
                        : null,
                  },
                }}
                className="text-primary hover:underline"
              >
                Sign up
              </Link>
            </p>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
}
