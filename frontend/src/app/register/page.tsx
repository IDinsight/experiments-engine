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
import GoogleLogin, {
  NEXT_PUBLIC_GOOGLE_LOGIN_CLIENT_ID,
} from "@/components/auth/GoogleLogin";
import { Flex } from "@radix-ui/themes";
import { useState } from "react";
import { apiCalls } from "@/utils/api";
import { useRouter } from "next/navigation";

import { useToast } from "@/hooks/use-toast";
import logoLight from "@/public/logo_light.svg";
import logoDark from "@/public/logo_dark.svg";
import Image from "next/image";

const formSchema = z.object({
  firstName: z.string().min(1, {
    message: "First name is required.",
  }),
  lastName: z.string().min(1, {
    message: "Last name is required.",
  }),
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
      firstName: "",
      lastName: "",
      email: "",
      password: "",
      confirm_password: "",
    },
  });

  const router = useRouter();
  const { loginGoogle, loginError } = useAuth();
  const [errorState, setErrorState] = useState<string | null>(null);

  const { toast } = useToast();

  async function onSubmit(values: z.infer<typeof formSchema>) {
    if (values.password !== values.confirm_password) {
      setErrorState("Passwords do not match!");
      return;
    }

    try {
      await apiCalls.registerUser(
        values.firstName,
        values.lastName,
        values.email,
        values.password
      );

      toast({
        title: "Success!",
        description: "Login created successfully. See email for verification.",
        variant: "success",
      });
      router.push("/login");
    } catch (error: unknown) {
      if (
        error instanceof Error &&
        (error as { status?: number }).status === 400
      ) {
        setErrorState("User with that username already exists.");
      } else {
        setErrorState(
          `An unexpected error occurred. Please try again later ${error}.`
        );
      }
    }
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
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-purple-50 to-blue-100 dark:from-black dark:to-blue-950 p-4">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-2xl"
        key="register-form-container"
      >
        <Card className="lg:min-w-2xl">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-semibold text-center">
              <div className="mb-5 flex justify-center">
                <Image
                  src={logoLight}
                  alt="Logo"
                  className="dark:hidden"
                  width={400}
                  height={81}
                />
                <Image
                  src={logoDark}
                  alt="Logo"
                  className="hidden dark:block"
                  width={400}
                  height={81}
                />
              </div>
              Welcome
            </CardTitle>
            <CardDescription className="text-center">
              Enter your information to register
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                {/* First Name and Last Name in the same row */}
                <div className="flex flex-col sm:grid sm:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="firstName"
                    render={({ field }) => (
                      <FormItem>
                        <div className="flex justify-between h-5">
                          <FormLabel>First Name</FormLabel>
                          <FormMessage className="leading-none" />
                        </div>
                        <FormControl>
                          <Input placeholder="John" {...field} />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="lastName"
                    render={({ field }) => (
                      <FormItem>
                        <div className="flex justify-between h-5">
                          <FormLabel>Last Name</FormLabel>
                          <FormMessage className="leading-none" />
                        </div>
                        <FormControl>
                          <Input placeholder="Doe" {...field} />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex justify-between h-5">
                        <FormLabel>Email</FormLabel>
                        <FormMessage className="leading-none" />
                      </div>
                      <FormControl>
                        <Input placeholder="you@example.com" {...field} />
                      </FormControl>
                    </FormItem>
                  )}
                />

                {/* Password and Confirm Password in the same row */}
                <div className="flex flex-col sm:grid sm:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <div className="flex justify-between gap-5 h-5">
                          <FormLabel>Password</FormLabel>
                          <FormMessage className="leading-none text-right" />
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
                        <div className="flex justify-between h-5 gap-5">
                          <FormLabel>Confirm</FormLabel>
                          <FormMessage className="leading-none text-right" />
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
                </div>

                <Button type="submit" className="w-full">
                  Register
                </Button>

                {/* Render loginError if it exists */}
                <FormMessage>
                  <span className="text-destructive">
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
