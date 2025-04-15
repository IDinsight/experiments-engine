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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import GoogleLogin, { NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID } from "@/components/auth/GoogleLogin";
import { Flex } from "@radix-ui/themes";
import { useState } from "react";
import { apiCalls } from "@/utils/api";
import { useRouter } from "next/navigation";

const formSchema = z.object({
  email: z.string().email({
    message: "Please enter a valid email address.",
  }),
  password: z.string().min(4, {
    message: "Password must be at least 4 characters long.",
  }),
  confirm_password: z.string().min(4, {
    message: "Password must be at least 4 characters long.",
  }),
});

export default function LoginPage() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  const router = useRouter();
  const { loginGoogle, loginError } = useAuth();
  const [errorState, setErrorState] = useState<string | null>(null);

  async function onSubmit(values: z.infer<typeof formSchema>) {
    if (values.password !== values.confirm_password) {
      setErrorState("Passwords do not match!");
    }

    try {
      await apiCalls.registerUser(values.email, values.password);
      router.push("/login");
    } catch (error: unknown) {
      if (error instanceof Error && (error as { status?: number }).status === 400) {
        setErrorState("User with that username already exists.");
      } else {
        setErrorState("An unexpected error occurred. Please try again later.");
      }
    }
  }

  const handleGoogleLogin = (response: google.accounts.id.CredentialResponse) => {
    loginGoogle({
      client_id: NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID,
      credential: response.credential,
    });
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-100 p-4">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">
              Welcome
            </CardTitle>
            <CardDescription className="text-center">
              Enter your email and password to register
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
                        <FormMessage />
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
                <FormField
                  control={form.control}
                  name="confirm_password"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex justify-between h-5">
                        <FormLabel>Confirm password</FormLabel>
                        <FormMessage />
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
                <Button type="submit" className="w-full">
                  Register
                </Button>

                {/* Render loginError if it exists */}
                <FormMessage>
                  <span className="text-red-500">
                    {loginError ? loginError : "\u00A0"}
                    {errorState ? errorState : "\u00A0"}
                  </span>
                </FormMessage>
              </form>
            </Form>
            <Flex direction="column" align="center" justify="center">
              <p className="pb-4 text-sm text-white-700">or</p>
              <GoogleLogin
                type="signup_with"
                handleCredentialResponse={handleGoogleLogin}
              />
            </Flex>
          </CardContent>
          <CardFooter className="flex justify-center">
            <p className="text-sm text-muted-foreground">
              {"Already have an account? "}
              <Link href="/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
}
